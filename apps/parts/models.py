from django.db import models
from apps.accounts.models import Team, User
from apps.planes.models import AIRCRAFT_TYPES
from django.core.exceptions import ValidationError

# Create your models here.

PART_TYPES = (
    ('wing', 'Kanat'),
    ('body', 'Gövde'),
    ('tail', 'Kuyruk'),
    ('avionics', 'Aviyonik'),
)

class Part(models.Model):
    part_type = models.CharField(max_length=50, choices=PART_TYPES)
    aircraft_type = models.CharField(max_length=50, choices=AIRCRAFT_TYPES, default='TB2')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_in_aircraft = models.ForeignKey('planes.Aircraft', on_delete=models.SET_NULL, null=True, blank=True)
    is_recycled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_part_type_display()} - {self.get_aircraft_type_display()} - {self.id}"
    
    @property
    def is_in_assembly(self):
        """Check if this part is assigned to an assembly process"""
        # Import here to avoid circular import
        from apps.assembly.models import AssemblyPart
        return AssemblyPart.objects.filter(part=self).exists()
    
    @property
    def is_in_use(self):
        """Check if this part is either in an aircraft or assigned to an assembly"""
        return self.used_in_aircraft is not None or self.is_in_assembly
    
    def clean(self):
        """Validate that a part cannot be recycled if it's in use"""
        if self.is_recycled and self.is_in_use:
            raise ValidationError("Cannot recycle a part that is in use")
        
        return super().clean()