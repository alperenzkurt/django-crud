from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

TEAM_TYPES = (
    ('wing', 'Kanat Takımı'),
    ('body', 'Gövde Takımı'),
    ('tail', 'Kuyruk Takımı'),
    ('avionics', 'Aviyonik Takımı'),
    ('assembly', 'Montaj Takımı'),
)

# Mapping between team types and part types
TEAM_TO_PART_TYPE = {
    'wing': 'wing',
    'body': 'body',
    'tail': 'tail',
    'avionics': 'avionics',
    'assembly': None  # Assembly team doesn't produce parts
}

class Team(models.Model):
    name = models.CharField(max_length=100)
    team_type = models.CharField(max_length=50, choices=TEAM_TYPES, default='assembly')

    def __str__(self):
        return self.name
    
    """Check if team can produce this type of part"""
    def can_produce_part(self, part_type):
        # Assembly team can't produce parts
        if self.team_type == 'assembly':
            return False
            
        # Teams can only produce parts matching their type
        allowed_part_type = TEAM_TO_PART_TYPE.get(self.team_type)
        return allowed_part_type == part_type

class User(AbstractUser):
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username
