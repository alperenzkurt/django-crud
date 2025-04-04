from rest_framework import serializers
from .models import Part
from apps.accounts.models import User, Team
from apps.assembly.models import AssemblyPart

class PartSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    part_type_display = serializers.SerializerMethodField()
    aircraft_type_display = serializers.SerializerMethodField()
    is_in_use = serializers.SerializerMethodField()
    
    class Meta:
        model = Part
        fields = ['id', 'part_type', 'part_type_display', 'aircraft_type', 'aircraft_type_display', 
                  'team', 'team_name', 'creator', 'creator_name', 'created_at', 'used_in_aircraft', 
                  'is_recycled', 'is_in_use']
        read_only_fields = ['team', 'creator']
        
    def get_team_name(self, obj):
        return obj.team.name if obj.team else None
        
    def get_creator_name(self, obj):
        return obj.creator.username if obj.creator else None
        
    def get_part_type_display(self, obj):
        return obj.get_part_type_display()
        
    def get_aircraft_type_display(self, obj):
        return obj.get_aircraft_type_display()
    
    def get_is_in_use(self, obj):
        """
        Returns True if the part is either:
        1. Used in a completed aircraft (used_in_aircraft is not None)
        2. Assigned to an in-progress assembly
        """
        if obj.used_in_aircraft:
            return True
        
        # Check if part is in an assembly (even if not in a completed aircraft)
        return AssemblyPart.objects.filter(part=obj).exists()
