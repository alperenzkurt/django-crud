from django.db import models
from apps.accounts.models import User
from apps.planes.models import Aircraft, AIRCRAFT_TYPES
from apps.parts.models import Part

# Create your models here.
class AssemblyProcess(models.Model):
    """
    Tracks an aircraft assembly process that might span multiple sessions
    and involve multiple assemblers
    """
    STATUS_CHOICES = (
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    )
    
    aircraft_type = models.CharField(max_length=50, choices=AIRCRAFT_TYPES)
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='started_assemblies')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_assemblies')
    start_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    aircraft = models.OneToOneField(Aircraft, on_delete=models.SET_NULL, null=True, blank=True, related_name='assembly_process')
    
    def __str__(self):
        return f"Assembly of {self.aircraft_type} - {self.id} ({self.get_status_display()})"
    
    @property
    def is_complete(self):
        return self.status == 'completed'
    
    @property
    def assigned_parts(self):
        """Returns all parts assigned to this assembly process"""
        return self.assemblypart_set.all()
    
    def get_missing_parts(self):
        """Returns a list of part types that are missing from this assembly"""
        assigned_part_types = self.assemblypart_set.values_list('part__part_type', flat=True)
        all_part_types = ['wing', 'body', 'tail', 'avionics']
        return [pt for pt in all_part_types if pt not in assigned_part_types]

class AssemblyPart(models.Model):
    """
    Links a part to an assembly process
    """
    assembly = models.ForeignKey(AssemblyProcess, on_delete=models.CASCADE)
    part = models.OneToOneField(Part, on_delete=models.CASCADE)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.part.get_part_type_display()} for {self.assembly}"
    
    class Meta:
        unique_together = ('assembly', 'part')

class AssemblyLog(models.Model):
    """
    Tracks actions performed during the assembly process
    """
    assembly = models.ForeignKey(AssemblyProcess, on_delete=models.CASCADE)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ACTION_CHOICES = (
        ('started', 'Montaj Başlatıldı'),
        ('added_part', 'Parça Eklendi'),
        ('removed_part', 'Parça Çıkarıldı'),
        ('completed', 'Montaj Tamamlandı'),
        ('cancelled', 'Montaj İptal Edildi'),
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    part = models.ForeignKey(Part, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.assembly}"
