from django.db import models

# Create your models here.
AIRCRAFT_TYPES = (
    ('TB2', 'TB2'),
    ('TB3', 'TB3'),
    ('AKINCI', 'AKINCI'),
    ('KIZILELMA', 'KIZILELMA'),
)

class Aircraft(models.Model):
    aircraft_type = models.CharField(max_length=50, choices=AIRCRAFT_TYPES)
    assembled_at = models.DateTimeField(auto_now_add=True)
    # You can add more fields if needed (e.g., production log)

    def __str__(self):
        return f"{self.aircraft_type} - {self.id}"
