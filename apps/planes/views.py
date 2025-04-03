from django.shortcuts import render

#custom
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.planes.models import Aircraft
from apps.parts.models import Part
from django.db import transaction

# Create your views here.
class AssembleAircraftView(APIView):
    def post(self, request, *args, **kwargs):
        aircraft_type = request.data.get('aircraft_type')
        part_ids = request.data.get('parts', [])  # Expected list of part IDs
        
        # Expected mapping: { 'wing': <id>, 'body': <id>, 'tail': <id>, 'avionics': <id> }
        required_parts = {
            'wing': None,
            'body': None,
            'tail': None,
            'avionics': None,
        }

        with transaction.atomic():
            for part in Part.objects.filter(id__in=part_ids):
                if part.is_recycled or part.used_in_aircraft:
                    return Response({"error": "Part already used or recycled"}, status=status.HTTP_400_BAD_REQUEST)
                required_parts[part.part_type] = part

            if None in required_parts.values():
                return Response({"error": "Missing required parts"}, status=status.HTTP_400_BAD_REQUEST)

            # Create the aircraft
            aircraft = Aircraft.objects.create(aircraft_type=aircraft_type)
            # Link parts to the new aircraft
            for part in required_parts.values():
                part.used_in_aircraft = aircraft
                part.save()
            
            return Response({"message": "Aircraft assembled", "aircraft_id": aircraft.id}, status=status.HTTP_201_CREATED)
