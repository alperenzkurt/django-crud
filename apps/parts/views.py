from django.shortcuts import render

#custom
from rest_framework import viewsets
from .models import Part
from .serializers import PartSerializer
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class PartViewSet(viewsets.ModelViewSet):
    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = [IsAuthenticated]
