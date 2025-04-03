from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class Team(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class User(AbstractUser):
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username
