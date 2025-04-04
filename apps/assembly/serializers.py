from rest_framework import serializers
from apps.assembly.models import AssemblyProcess, AssemblyPart, AssemblyLog
from apps.parts.models import Part
from apps.planes.models import Aircraft

class PartBriefSerializer(serializers.ModelSerializer):
    """Simplified part serializer for use in assembly views"""
    part_type_display = serializers.CharField(source='get_part_type_display', read_only=True)
    aircraft_type_display = serializers.CharField(source='get_aircraft_type_display', read_only=True)
    creator_info = serializers.SerializerMethodField()
    team_info = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%d.%m.%Y")
    
    class Meta:
        model = Part
        fields = ['id', 'part_type', 'part_type_display', 'aircraft_type', 
                  'aircraft_type_display', 'created_at', 'creator', 'creator_info', 'team_info']
    
    def get_creator_info(self, obj):
        if not obj.creator:
            return None
        return {
            'id': obj.creator.id,
            'username': obj.creator.username,
            'full_name': obj.creator.get_full_name()
        }
    
    def get_team_info(self, obj):
        if not obj.team:
            return None
        return {
            'id': obj.team.id,
            'name': obj.team.name,
            'team_type': obj.team.team_type
        }

class AssemblyPartSerializer(serializers.ModelSerializer):
    part = PartBriefSerializer(read_only=True)
    part_id = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.filter(used_in_aircraft__isnull=True, is_recycled=False),
        source='part',
        write_only=True
    )
    
    class Meta:
        model = AssemblyPart
        fields = ['id', 'part', 'part_id', 'added_by', 'added_at']
        read_only_fields = ['added_by', 'added_at']

class AssemblyLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AssemblyLog
        fields = ['id', 'action', 'action_display', 'action_by', 'timestamp', 'part', 'notes']
        read_only_fields = ['action_by', 'timestamp']

class AssemblyProcessSerializer(serializers.ModelSerializer):
    parts = AssemblyPartSerializer(source='assemblypart_set', many=True, read_only=True)
    logs = AssemblyLogSerializer(source='assemblylog_set', many=True, read_only=True)
    aircraft_type_display = serializers.CharField(source='get_aircraft_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    missing_parts = serializers.ListField(source='get_missing_parts', read_only=True)
    
    class Meta:
        model = AssemblyProcess
        fields = ['id', 'aircraft_type', 'aircraft_type_display', 'started_by', 'completed_by', 
                  'start_date', 'completion_date', 'status', 'status_display', 'aircraft', 
                  'parts', 'logs', 'missing_parts']
        read_only_fields = ['started_by', 'completed_by', 'start_date', 'completion_date', 'aircraft']
        
    def validate(self, data):
        # Ensure the aircraft type is valid
        aircraft_type = data.get('aircraft_type')
        if not aircraft_type:
            raise serializers.ValidationError({"aircraft_type": "This field is required"})
        return data

class AircraftDetailSerializer(serializers.ModelSerializer):
    """Detailed aircraft serializer including parts"""
    parts = PartBriefSerializer(source='part_set', many=True, read_only=True)
    aircraft_type_display = serializers.CharField(source='get_aircraft_type_display', read_only=True)
    
    class Meta:
        model = Aircraft
        fields = ['id', 'aircraft_type', 'aircraft_type_display', 'assembled_at', 'parts'] 