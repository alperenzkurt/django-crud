from django.shortcuts import render

#custom
from rest_framework import viewsets, status
from .models import Part
from .serializers import PartSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q

# Create your views here.
class PartViewSet(viewsets.ModelViewSet):
    serializer_class = PartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter parts based on user's team
        Assembly team can see all parts, other teams only see their own parts
        """
        user = self.request.user
        if not user.team:
            return Part.objects.none()
            
        if user.team.team_type == 'assembly':
            return Part.objects.all()
        else:
            return Part.objects.filter(team=user.team)

    def perform_create(self, serializer):
        """Ensure teams can only create parts of their type"""
        user = self.request.user
        if not user.team:
            raise PermissionDenied("Bu kullanıcı bir takıma atanmamış.")
            
        part_type = self.request.data.get('part_type')
        
        # Check if team can produce this part type
        if not user.team.can_produce_part(part_type):
            raise PermissionDenied(f"Bu takım {dict(Part.PART_TYPES).get(part_type)} üretemez.")
            
        # Set the team automatically based on the user's team
        serializer.save(team=user.team)
        
    def perform_update(self, serializer):
        """Prevent changing part's type to one the team can't produce"""
        user = self.request.user
        part = self.get_object()
        
        # Only the team that created the part can update it
        if part.team != user.team and user.team.team_type != 'assembly':
            raise PermissionDenied("Sadece parçayı üreten takım güncelleyebilir.")
            
        part_type = self.request.data.get('part_type')
        if part_type and part_type != part.part_type and not user.team.can_produce_part(part_type):
            raise PermissionDenied(f"Bu takım {dict(Part.PART_TYPES).get(part_type)} üretemez.")
            
        serializer.save()
        
    def perform_destroy(self, instance):
        """Only allow teams to recycle their own parts"""
        user = self.request.user
        
        # Only the team that created the part can delete/recycle it
        if instance.team != user.team and user.team.team_type != 'assembly':
            raise PermissionDenied("Sadece parçayı üreten takım geri dönüşüme gönderebilir.")
            
        # If already used in an aircraft, can't be recycled
        if instance.used_in_aircraft:
            raise PermissionDenied("Uçakta kullanılan parçalar geri dönüşüme gönderilemez.")
            
        instance.delete()
