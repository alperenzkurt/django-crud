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
    
    """Get all assembly processes"""
    def get_queryset(self):
        return AssemblyProcess.objects.all().order_by('-start_date')
    
    """List method to add formatted data to each item"""
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        # Add explicit display values to each item
        for item in data:
            assembly = AssemblyProcess.objects.get(id=item['id'])
            item['get_status_display'] = assembly.get_status_display()
            item['get_aircraft_type_display'] = assembly.get_aircraft_type_display()
            
            # Format dates
            if item['start_date']:
                item['start_date'] = assembly.start_date.strftime('%d.%m.%Y %H:%M')
            
            if item['completion_date']:
                item['completion_date'] = assembly.completion_date.strftime('%d.%m.%Y %H:%M')
                
            # Add user information
            if assembly.started_by:
                item['started_by'] = assembly.started_by.username
            
            if assembly.completed_by:
                item['completed_by'] = assembly.completed_by.username

        return Response(data)
    
    """Create a new assembly process and log it"""
    def perform_create(self, serializer):
        process = serializer.save(started_by=self.request.user)
        # Create log entry for starting the assembly
        AssemblyLog.objects.create(
            assembly=process,
            action_by=self.request.user,
            action='started'
        )
    
    """Override retrieve to add formatted data"""
    def retrieve(self, request, *args, **kwargs):
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
    
    """Add parts to the assembly process"""
    @action(detail=True, methods=['post'])
    def add_part(self, request, pk=None):
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
    
    """Remove a part from the assembly process"""
    @action(detail=True, methods=['post'])
    def remove_part(self, request, pk=None):
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
    
    """Complete an assembly process, creating an aircraft"""
    @action(detail=True, methods=['post'])
    def complete_assembly(self, request, pk=None):
        assembly = self.get_object()
        
        # Check if assembly is already completed
        if assembly.status != 'in_progress':
            return Response(
                {"error": "Assembly is already completed or cancelled."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if all required parts are present
        required_parts = set(part_type for part_type, _ in PART_TYPES)
        existing_part_types = set(assembly.assemblypart_set.values_list('part__part_type', flat=True))
        
        missing_parts = required_parts - existing_part_types
        if missing_parts:
            # Format the missing parts list with display names
            missing_part_names = [dict(PART_TYPES)[part_type] for part_type in missing_parts]
            return Response({
                "error": f"Assembly is incomplete. Missing parts: {', '.join(missing_part_names)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # All parts present, complete the assembly
        with transaction.atomic():
            # Create an Aircraft object
            aircraft = Aircraft.objects.create(
                aircraft_type=assembly.aircraft_type
            )
            
            # Update all parts to mark them as used in this aircraft
            for assembly_part in assembly.assemblypart_set.all():
                part = assembly_part.part
                part.used_in_aircraft = aircraft
                part.save(update_fields=['used_in_aircraft'])
            
            # Update the assembly status
            assembly.status = 'completed'
            assembly.completed_by = request.user
            assembly.completion_date = timezone.now()
            assembly.save()
            
            # Create log entry
            AssemblyLog.objects.create(
                assembly=assembly,
                action_by=request.user,
                action='completed',
                notes=f"Montaj tamamlandı. Uçak ID: {aircraft.id}"
            )
        
        return Response({
            "message": "Assembly completed successfully",
            "aircraft_id": aircraft.id
        }, status=status.HTTP_200_OK)
    
    """Cancel an assembly process, returning parts to inventory"""
    @action(detail=True, methods=['post'])
    def cancel_assembly(self, request, pk=None):
        assembly = self.get_object()
        
        # Check if assembly is already completed
        if assembly.status != 'in_progress':
            return Response(
                {"error": "Assembly is already completed or cancelled."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Update the assembly status
            assembly.status = 'cancelled'
            assembly.completed_by = request.user
            assembly.completion_date = timezone.now()
            assembly.save()
            
            # Create log entry
            AssemblyLog.objects.create(
                assembly=assembly,
                action_by=request.user,
                action='cancelled',
                notes="Montaj iptal edildi."
            )
        
        return Response({
            "message": "Assembly cancelled successfully"
        }, status=status.HTTP_200_OK)


class AvailablePartsView(APIView):
    """View to list all available parts for a specific aircraft type"""
    permission_classes = [IsAssemblyTeamMember]
    
    """Get available parts for assembly by aircraft type"""
    def get(self, request, aircraft_type=None):
        if not aircraft_type:
            return Response({"error": "Aircraft type is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get available parts for this aircraft type not in use
        available_parts = Part.objects.filter(
            aircraft_type=aircraft_type,
            used_in_aircraft__isnull=True,
            is_recycled=False
        ).exclude(
            id__in=AssemblyPart.objects.values_list('part_id', flat=True)
        )
        
        # Group by part type
        parts_by_type = {}
        for part_type, name in PART_TYPES:
            parts = available_parts.filter(part_type=part_type)
            parts_data = []
            
            for part in parts:
                parts_data.append({
                    'id': part.id,
                    'team': part.team.name if part.team else None,
                    'creator': part.creator.username if part.creator else None,
                    'created_at': part.created_at.strftime('%d.%m.%Y %H:%M')
                })
            
            parts_by_type[part_type] = {
                'name': name,
                'parts': parts_data,
                'count': len(parts_data)
            }
        
        return Response(parts_by_type)


class CompletedAircraftViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for completed aircraft"""
    serializer_class = AircraftDetailSerializer
    permission_classes = [IsAssemblyTeamMember]
    
    """Get all aircraft that have all required parts"""
    def get_queryset(self):
        return Aircraft.objects.all().order_by('-id')
        
    """List method to add formatted data to each item"""
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        # Add explicit display values to each item
        for item in data:
            aircraft = Aircraft.objects.get(id=item['id'])
            item['get_aircraft_type_display'] = aircraft.get_aircraft_type_display()
            item['aircraft_type_display'] = aircraft.get_aircraft_type_display()
            
            # Format dates
            if item['assembled_at']:
                item['assembled_at'] = aircraft.assembled_at.strftime('%d.%m.%Y %H:%M')
                
            # Add parts count
            item['parts_count'] = aircraft.part_set.count()

        return Response(data)


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
