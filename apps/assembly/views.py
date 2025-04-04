from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db import transaction

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User, Team
from apps.parts.models import Part, PART_TYPES
from apps.planes.models import Aircraft
from apps.assembly.models import AssemblyProcess, AssemblyPart, AssemblyLog
from apps.assembly.serializers import (
    AssemblyProcessSerializer, 
    AssemblyPartSerializer,
    AssemblyLogSerializer,
    AircraftDetailSerializer
)

# Permission class to check if user is in assembly team
class IsAssemblyTeamMember(permissions.BasePermission):
    """
    Custom permission to only allow members of the assembly team.
    """
    message = "You must be a member of the assembly team to perform this action."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.team and request.user.team.team_type == 'assembly'


class AssemblyProcessViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Assembly Processes.
    Only assembly team members can access this.
    """
    serializer_class = AssemblyProcessSerializer
    permission_classes = [IsAssemblyTeamMember]
    
    def get_queryset(self):
        """Get all assembly processes"""
        return AssemblyProcess.objects.all().order_by('-start_date')
    
    def perform_create(self, serializer):
        """Create a new assembly process and log it"""
        process = serializer.save(started_by=self.request.user)
        # Create log entry for starting the assembly
        AssemblyLog.objects.create(
            assembly=process,
            action_by=self.request.user,
            action='started'
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to add formatted data"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add explicit display values
        data['get_status_display'] = instance.get_status_display()
        data['get_aircraft_type_display'] = instance.get_aircraft_type_display()
        
        # Add user information
        if instance.started_by:
            data['started_by'] = {
                'username': instance.started_by.username,
                'id': instance.started_by.id
            }
        
        if instance.completed_by:
            data['completed_by'] = {
                'username': instance.completed_by.username,
                'id': instance.completed_by.id
            }
        
        # Format dates
        if instance.start_date:
            data['start_date'] = instance.start_date.strftime('%d.%m.%Y %H:%M')
        
        if instance.completion_date:
            data['completion_date'] = instance.completion_date.strftime('%d.%m.%Y %H:%M')
        
        # Format logs with user and part information
        logs = instance.assemblylog_set.all().order_by('-timestamp')
        log_data = []
        
        for log in logs:
            log_entry = {
                'action': log.action,
                'action_display': log.get_action_display(),
                'timestamp': log.timestamp.strftime('%d.%m.%Y %H:%M'),
                'notes': log.notes,
            }
            
            # Add action_by information
            if log.action_by:
                log_entry['action_by'] = {
                    'username': log.action_by.username,
                    'id': log.action_by.id
                }
            else:
                log_entry['action_by'] = {
                    'username': 'Bilinmeyen Kullanıcı'
                }
            
            # Add part information if available
            if log.part:
                log_entry['part'] = {
                    'id': log.part.id,
                    'part_type': log.part.part_type,
                    'part_type_display': log.part.get_part_type_display()
                }
            
            log_data.append(log_entry)
        
        data['logs'] = log_data
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def add_part(self, request, pk=None):
        """Add parts to the assembly process"""
        assembly = self.get_object()
        
        # Check if assembly is already completed
        if assembly.status != 'in_progress':
            return Response(
                {"error": "Cannot add parts to a completed or cancelled assembly"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if we're getting a single part or multiple parts
        if 'part_id' in request.data:
            # Handle single part case
            part_ids = [request.data['part_id']]
        elif 'part_ids' in request.data and isinstance(request.data['part_ids'], list):
            # Handle multiple parts case
            part_ids = request.data['part_ids']
        else:
            return Response(
                {"error": "part_id or part_ids list is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        added_parts = []
        errors = []
        
        with transaction.atomic():
            for part_id in part_ids:
                # Validate part data
                part_data = {'part_id': part_id}
                serializer = AssemblyPartSerializer(data=part_data)
                
                if not serializer.is_valid():
                    errors.append({
                        "part_id": part_id,
                        "errors": serializer.errors
                    })
                    continue
                
                part = serializer.validated_data['part']
                
                # Check if part is compatible with the aircraft type
                if part.aircraft_type != assembly.aircraft_type:
                    errors.append({
                        "part_id": part_id,
                        "error": f"This part ({part.get_part_type_display()}) is for {part.get_aircraft_type_display()}, "
                                f"not for {assembly.get_aircraft_type_display()}"
                    })
                    continue
                
                # Check if part is already assigned to any assembly
                if AssemblyPart.objects.filter(part=part).exists():
                    errors.append({
                        "part_id": part_id,
                        "error": f"This part is already used in another assembly"
                    })
                    continue
                
                # Check if there's already a part of this type in the assembly
                if AssemblyPart.objects.filter(assembly=assembly, part__part_type=part.part_type).exists():
                    errors.append({
                        "part_id": part_id,
                        "error": f"This assembly already has a {part.get_part_type_display()} part"
                    })
                    continue
                
                try:
                    # Add part to the assembly
                    assembly_part = serializer.save(
                        assembly=assembly,
                        added_by=request.user
                    )
                    
                    # Update the assembly last modified info
                    assembly.completed_by = request.user
                    assembly.completion_date = timezone.now()
                    assembly.save()
                    
                    # Create log entry
                    AssemblyLog.objects.create(
                        assembly=assembly,
                        action_by=request.user,
                        action='added_part',
                        part=part,
                        notes=f"Eklenen parça: {part.get_part_type_display()}"
                    )
                    
                    added_parts.append(AssemblyPartSerializer(assembly_part).data)
                except Exception as e:
                    errors.append({
                        "part_id": part_id,
                        "error": str(e)
                    })
            
            # If we weren't able to add any parts, roll back the transaction
            if not added_parts and errors:
                # Force a rollback by raising an exception
                raise serializers.ValidationError(errors)
        
        # Return the results
        return Response({
            "added_parts": added_parts,
            "errors": errors
        }, status=status.HTTP_201_CREATED if added_parts else status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def remove_part(self, request, pk=None):
        """Remove a part from the assembly process"""
        assembly = self.get_object()
        
        # Check if assembly is already completed
        if assembly.status != 'in_progress':
            return Response(
                {"error": "Cannot remove parts from a completed or cancelled assembly"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        part_id = request.data.get('part_id')
        if not part_id:
            return Response({"error": "Part ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assembly_part = AssemblyPart.objects.get(assembly=assembly, part_id=part_id)
            part = assembly_part.part
            
            with transaction.atomic():
                # Log the removal
                AssemblyLog.objects.create(
                    assembly=assembly,
                    action_by=request.user,
                    action='removed_part',
                    part=part,
                    notes=f"İptal sırasında çıkarılan parça: {part.get_part_type_display()}"
                )
                
                # Remove the part from assembly
                assembly_part.delete()
                
                # Update the assembly last modified info
                assembly.completed_by = request.user
                assembly.completion_date = timezone.now()
                assembly.save()
            
            return Response({"message": f"{part.get_part_type_display()} part removed from assembly"})
        
        except AssemblyPart.DoesNotExist:
            return Response({"error": "Part not found in this assembly"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def complete_assembly(self, request, pk=None):
        """Complete the assembly process and create the aircraft"""
        assembly = self.get_object()
        
        # Check if assembly is in progress
        if assembly.status != 'in_progress':
            return Response(
                {"error": "Only in-progress assemblies can be completed"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if all required parts are present
        missing_parts = assembly.get_missing_parts()
        if missing_parts:
            missing_parts_display = [dict(PART_TYPES).get(pt) for pt in missing_parts]
            return Response(
                {"error": f"Cannot complete assembly. Missing parts: {', '.join(missing_parts_display)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create aircraft
            aircraft = Aircraft.objects.create(aircraft_type=assembly.aircraft_type)
            
            # Link parts to the aircraft
            for assembly_part in assembly.assemblypart_set.all():
                part = assembly_part.part
                part.used_in_aircraft = aircraft
                part.save()
            
            # Update assembly status
            assembly.status = 'completed'
            assembly.completed_by = request.user
            assembly.completion_date = timezone.now()
            assembly.aircraft = aircraft
            assembly.save()
            
            # Create log entry
            AssemblyLog.objects.create(
                assembly=assembly,
                action_by=request.user,
                action='completed',
                notes=f"{assembly.get_aircraft_type_display()} montajı tamamlandı"
            )
            
            # Return the aircraft details
            return Response(
                {
                    "message": f"{assembly.get_aircraft_type_display()} successfully assembled",
                    "aircraft": AircraftDetailSerializer(aircraft).data
                },
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'])
    def cancel_assembly(self, request, pk=None):
        """Cancel an in-progress assembly"""
        assembly = self.get_object()
        
        # Check if assembly is in progress
        if assembly.status != 'in_progress':
            return Response(
                {"error": "Only in-progress assemblies can be cancelled"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Get all parts currently in the assembly
            assembly_parts = AssemblyPart.objects.filter(assembly=assembly)
            
            # Create log entries for each part removal
            for assembly_part in assembly_parts:
                part = assembly_part.part
                AssemblyLog.objects.create(
                    assembly=assembly,
                    action_by=request.user,
                    action='removed_part',
                    part=part,
                    notes=f"İptal sırasında çıkarılan parça: {part.get_part_type_display()}"
                )
            
            # Delete all assembly-part relationships, which returns parts to the available pool
            assembly_parts.delete()
            
            # Update assembly status
            assembly.status = 'cancelled'
            assembly.completed_by = request.user
            assembly.completion_date = timezone.now()
            assembly.save()
            
            # Create cancel log entry
            AssemblyLog.objects.create(
                assembly=assembly,
                action_by=request.user,
                action='cancelled',
                notes=request.data.get('reason', 'No reason provided')
            )
        
        return Response({"message": "Assembly cancelled and all parts returned to inventory"}, status=status.HTTP_200_OK)


class AvailablePartsView(APIView):
    """View to list all available parts for a specific aircraft type"""
    permission_classes = [IsAssemblyTeamMember]
    
    def get(self, request, aircraft_type=None):
        if not aircraft_type:
            return Response({"error": "Aircraft type is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get available parts (not used in any aircraft and not recycled and not assigned to any assembly)
        parts = Part.objects.filter(
            aircraft_type=aircraft_type,
            used_in_aircraft__isnull=True,
            is_recycled=False
        ).exclude(
            assemblypart__isnull=False  # Exclude parts that are in any assembly
        )
        
        # Group by part type
        parts_by_type = {}
        for part_type, _ in PART_TYPES:
            parts_by_type[part_type] = Part.objects.filter(
                part_type=part_type,
                aircraft_type=aircraft_type,
                used_in_aircraft__isnull=True,
                is_recycled=False
            ).exclude(
                assemblypart__isnull=False  # Exclude parts that are in any assembly
            ).count()
        
        # Get count of existing aircraft of this type
        aircraft_count = Aircraft.objects.filter(aircraft_type=aircraft_type).count()
        
        from apps.assembly.serializers import PartBriefSerializer
        return Response({
            "aircraft_type": aircraft_type,
            "existing_aircraft_count": aircraft_count,
            "available_parts": parts_by_type,
            "parts": PartBriefSerializer(parts, many=True).data
        })


class CompletedAircraftViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for completed aircraft"""
    serializer_class = AircraftDetailSerializer
    permission_classes = [IsAssemblyTeamMember]
    
    def get_queryset(self):
        """Get all completed aircraft"""
        return Aircraft.objects.all().order_by('-assembled_at')


# Template Views
def assembly_list_view(request):
    """View for listing assembly processes and completed aircraft"""
    if not request.user.is_authenticated or not request.user.team or request.user.team.team_type != 'assembly':
        return render(request, '403.html', {'message': 'You must be a member of the assembly team to access this page.'})
    
    assemblies = AssemblyProcess.objects.all().order_by('-start_date')
    completed_aircraft = Aircraft.objects.all().order_by('-assembled_at')
    
    context = {
        'assemblies': assemblies,
        'completed_aircraft': completed_aircraft
    }
    
    return render(request, 'assembly/assembly_list.html', context)

def assembly_detail_view(request, pk):
    """View for assembly detail with interactive skeleton"""
    if not request.user.is_authenticated or not request.user.team or request.user.team.team_type != 'assembly':
        return render(request, '403.html', {'message': 'You must be a member of the assembly team to access this page.'})
    
    assembly = get_object_or_404(AssemblyProcess, pk=pk)
    
    # Prepare context with the assembly data
    serializer = AssemblyProcessSerializer(assembly)
    assembly_data = serializer.data
    
    # Add explicit display values to ensure they are available in the template
    assembly_data['get_status_display'] = assembly.get_status_display()
    assembly_data['get_aircraft_type_display'] = assembly.get_aircraft_type_display()
    
    # Add user information explicitly
    if assembly.started_by:
        assembly_data['started_by'] = {
            'username': assembly.started_by.username,
            'id': assembly.started_by.id
        }
    
    if assembly.completed_by:
        assembly_data['completed_by'] = {
            'username': assembly.completed_by.username,
            'id': assembly.completed_by.id
        }
    
    # Format dates properly
    if assembly.start_date:
        assembly_data['start_date'] = assembly.start_date.strftime('%d.%m.%Y %H:%M')
    
    if assembly.completion_date:
        assembly_data['completion_date'] = assembly.completion_date.strftime('%d.%m.%Y %H:%M')
    
    # Add the logs in reverse chronological order (most recent first)
    logs = assembly.assemblylog_set.all().order_by('-timestamp')
    log_data = []
    
    for log in logs:
        log_entry = {
            'action': log.action,
            'action_display': log.get_action_display(),
            'timestamp': log.timestamp.strftime('%d.%m.%Y %H:%M'),
            'notes': log.notes,
        }
        
        # Add action_by information
        if log.action_by:
            log_entry['action_by'] = {
                'username': log.action_by.username,
                'id': log.action_by.id
            }
        else:
            log_entry['action_by'] = {
                'username': 'Bilinmeyen Kullanıcı'
            }
        
        # Add part information if available
        if log.part:
            log_entry['part'] = {
                'id': log.part.id,
                'part_type': log.part.part_type,
                'part_type_display': log.part.get_part_type_display()
            }
        
        log_data.append(log_entry)
    
    assembly_data['logs'] = log_data
    
    context = {
        'assembly': assembly_data
    }
    
    return render(request, 'assembly/assembly_detail.html', context)

def aircraft_detail_view(request, pk):
    """View for completed aircraft detail"""
    if not request.user.is_authenticated or not request.user.team or request.user.team.team_type != 'assembly':
        return render(request, '403.html', {'message': 'You must be a member of the assembly team to access this page.'})
    
    aircraft = get_object_or_404(Aircraft, pk=pk)
    
    # Prepare context with the aircraft data
    serializer = AircraftDetailSerializer(aircraft)
    aircraft_data = serializer.data
    
    # Get assembly process data for this aircraft
    assembly_process = None
    started_by = None
    completed_by = None
    start_date = None
    completion_date = None
    
    try:
        assembly_process = aircraft.assembly_process
        if assembly_process:
            started_by = assembly_process.started_by
            completed_by = assembly_process.completed_by
            start_date = assembly_process.start_date
            completion_date = assembly_process.completion_date
    except:
        pass
    
    context = {
        'aircraft': aircraft_data,
        'assembly_process': assembly_process,
        'started_by': started_by,
        'completed_by': completed_by,
        'start_date': start_date,
        'completion_date': completion_date,
        'raw_aircraft': aircraft  # Pass the actual model instance
    }
    
    return render(request, 'assembly/aircraft_detail.html', context)
