from django.db import models
from apps.accounts.models import Team

# Create your models here.

PART_TYPES = (
    ('wing', 'Kanat'),
    ('body', 'Gövde'),
    ('tail', 'Kuyruk'),
    ('avionics', 'Aviyonik'),
)

class Part(models.Model):
    part_type = models.CharField(max_length=50, choices=PART_TYPES)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    used_in_aircraft = models.ForeignKey('planes.Aircraft', on_delete=models.SET_NULL, null=True, blank=True)
    is_recycled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_part_type_display()} - {self.id}"