from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.assembly.models import AssemblyProcess, AssemblyPart, AssemblyLog
from apps.parts.models import Part
from apps.planes.models import Aircraft
from apps.accounts.models import User, Team
from apps.assembly.views import IsAssemblyTeamMember


class AssemblyModelTests(TestCase):
    """Tests for the assembly models"""
    
    def setUp(self):
        # Create teams
        self.assembly_team = Team.objects.create(name='Assembly Team', team_type='assembly')
        self.wing_team = Team.objects.create(name='Wing Team', team_type='wing')
        self.body_team = Team.objects.create(name='Body Team', team_type='body')
        self.tail_team = Team.objects.create(name='Tail Team', team_type='tail')
        self.avionics_team = Team.objects.create(name='Avionics Team', team_type='avionics')
        
        # Create users
        self.assembler = User.objects.create_user(
            username='assembler',
            email='assembler@example.com',
            password='password',
            team=self.assembly_team
        )
        
        # Create an assembly process
        self.assembly_process = AssemblyProcess.objects.create(
            aircraft_type='TB2',
            started_by=self.assembler
        )
        
        # Create parts
        self.wing_part = Part.objects.create(
            part_type='wing',
            aircraft_type='TB2',
            team=self.wing_team,
            creator=self.assembler
        )
        
        self.body_part = Part.objects.create(
            part_type='body',
            aircraft_type='TB2',
            team=self.body_team,
            creator=self.assembler
        )
        
        self.tail_part = Part.objects.create(
            part_type='tail',
            aircraft_type='TB2',
            team=self.tail_team,
            creator=self.assembler
        )
        
        self.avionics_part = Part.objects.create(
            part_type='avionics',
            aircraft_type='TB2',
            team=self.avionics_team,
            creator=self.assembler
        )
    
    """Test string representation of AssemblyProcess objects"""
    def test_assembly_process_str_representation(self):
        expected = f"Assembly of TB2 - {self.assembly_process.id} (Devam Ediyor)"
        self.assertEqual(str(self.assembly_process), expected)
    
    """Test is_complete property for assembly process"""
    def test_assembly_is_complete_property(self):
        # Initially not complete
        self.assertFalse(self.assembly_process.is_complete)
        
        # Update to completed
        self.assembly_process.status = 'completed'
        self.assembly_process.save()
        
        # Now should be complete
        self.assertTrue(self.assembly_process.is_complete)
    
    """Test get_missing_parts method"""
    def test_assembly_get_missing_parts(self):
        # Initially all parts are missing
        self.assertEqual(set(self.assembly_process.get_missing_parts()), 
                         {'wing', 'body', 'tail', 'avionics'})
        
        # Add wing part
        AssemblyPart.objects.create(
            assembly=self.assembly_process,
            part=self.wing_part,
            added_by=self.assembler
        )
        
        # Now wing part should not be in missing parts
        self.assertEqual(set(self.assembly_process.get_missing_parts()), 
                         {'body', 'tail', 'avionics'})
        
        # Add all other parts
        AssemblyPart.objects.create(
            assembly=self.assembly_process,
            part=self.body_part,
            added_by=self.assembler
        )
        
        AssemblyPart.objects.create(
            assembly=self.assembly_process,
            part=self.tail_part,
            added_by=self.assembler
        )
        
        AssemblyPart.objects.create(
            assembly=self.assembly_process,
            part=self.avionics_part,
            added_by=self.assembler
        )
        
        # Now no parts should be missing
        self.assertEqual(self.assembly_process.get_missing_parts(), [])
    
    """Test assembly log creation"""
    def test_assembly_log_creation(self):
        # Create a log entry
        log = AssemblyLog.objects.create(
            assembly=self.assembly_process,
            action_by=self.assembler,
            action='started'
        )
        
        self.assertEqual(log.assembly, self.assembly_process)
        self.assertEqual(log.action_by, self.assembler)
        self.assertEqual(log.action, 'started')
        
        # Verify string representation
        expected = "Montaj Başlatıldı - " + str(self.assembly_process)
        self.assertEqual(str(log), expected)


class AssemblyAPITests(APITestCase):
    """Tests for assembly API endpoints"""
    
    def setUp(self):
        # Create teams
        self.assembly_team = Team.objects.create(name='Assembly Team', team_type='assembly')
        self.wing_team = Team.objects.create(name='Wing Team', team_type='wing')
        
        # Create users
        self.assembler = User.objects.create_user(
            username='assembler',
            email='assembler@example.com',
            password='password',
            team=self.assembly_team
        )
        
        self.wing_user = User.objects.create_user(
            username='wing_user',
            email='wing@example.com',
            password='password',
            team=self.wing_team
        )
        
        # Create client
        self.client = APIClient()
        
        # Create parts for assembly
        self.wing_part = Part.objects.create(
            part_type='wing',
            aircraft_type='TB2',
            team=self.wing_team,
            creator=self.wing_user
        )
        
        self.body_part = Part.objects.create(
            part_type='body',
            aircraft_type='TB2',
            team=Team.objects.create(name='Body Team', team_type='body'),
            creator=self.wing_user
        )
        
        self.tail_part = Part.objects.create(
            part_type='tail',
            aircraft_type='TB2',
            team=Team.objects.create(name='Tail Team', team_type='tail'),
            creator=self.wing_user
        )
        
        self.avionics_part = Part.objects.create(
            part_type='avionics',
            aircraft_type='TB2',
            team=Team.objects.create(name='Avionics Team', team_type='avionics'),
            creator=self.wing_user
        )
        
        # Create API endpoints
        self.assembly_list_url = reverse('assembly-process-list')
    
    """Test creating a new assembly process"""
    def test_create_assembly_process(self):
        # Login as assembly team member
        self.client.force_authenticate(user=self.assembler)
        
        # Create new assembly process
        data = {
            'aircraft_type': 'TB2'
        }
        response = self.client.post(self.assembly_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the assembly process was created
        self.assertEqual(AssemblyProcess.objects.count(), 1)
        assembly = AssemblyProcess.objects.first()
        self.assertEqual(assembly.aircraft_type, 'TB2')
        self.assertEqual(assembly.started_by, self.assembler)
        self.assertEqual(assembly.status, 'in_progress')
        
        # Verify that a log entry was created
        self.assertEqual(AssemblyLog.objects.count(), 1)
        log = AssemblyLog.objects.first()
        self.assertEqual(log.assembly, assembly)
        self.assertEqual(log.action, 'started')
        self.assertEqual(log.action_by, self.assembler)
    
    """Test that non-assembly team members cannot create assembly processes"""
    def test_non_assembly_team_cannot_create_assembly(self):
        # Login as wing team member
        self.client.force_authenticate(user=self.wing_user)
        
        # Try to create new assembly process
        data = {
            'aircraft_type': 'TB2'
        }
        response = self.client.post(self.assembly_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    """Test completing an assembly process and creating an aircraft"""
    def test_complete_assembly_process(self):
        # Create an assembly process with all parts
        assembly = AssemblyProcess.objects.create(
            aircraft_type='TB2',
            started_by=self.assembler
        )
        
        # Add all parts to the assembly
        AssemblyPart.objects.create(
            assembly=assembly,
            part=self.wing_part,
            added_by=self.assembler
        )
        
        AssemblyPart.objects.create(
            assembly=assembly,
            part=self.body_part,
            added_by=self.assembler
        )
        
        AssemblyPart.objects.create(
            assembly=assembly,
            part=self.tail_part,
            added_by=self.assembler
        )
        
        AssemblyPart.objects.create(
            assembly=assembly,
            part=self.avionics_part,
            added_by=self.assembler
        )
        
        # Login as assembly team member
        self.client.force_authenticate(user=self.assembler)
        
        # Complete the assembly
        complete_url = reverse('assembly-process-complete-assembly', args=[assembly.id])
        response = self.client.post(complete_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the assembly process was updated
        assembly.refresh_from_db()
        self.assertEqual(assembly.status, 'completed')
        self.assertIsNotNone(assembly.completion_date)
        self.assertEqual(assembly.completed_by, self.assembler)
        
        # Verify an aircraft was created
        self.assertEqual(Aircraft.objects.count(), 1)
        aircraft = Aircraft.objects.first()
        self.assertEqual(aircraft.aircraft_type, 'TB2')
        
        # Verify parts are assigned to the aircraft
        for part in [self.wing_part, self.body_part, self.tail_part, self.avionics_part]:
            part.refresh_from_db()
            self.assertEqual(part.used_in_aircraft, aircraft)


class AssemblyPermissionTests(TestCase):
    """Tests for assembly permissions"""
    
    def setUp(self):
        self.assembly_team = Team.objects.create(name='Assembly Team', team_type='assembly')
        self.wing_team = Team.objects.create(name='Wing Team', team_type='wing')
        
        self.assembler = User.objects.create_user(
            username='assembler',
            email='assembler@example.com',
            password='password',
            team=self.assembly_team
        )
        
        self.wing_user = User.objects.create_user(
            username='wing_user',
            email='wing@example.com',
            password='password',
            team=self.wing_team
        )
        
        self.permission = IsAssemblyTeamMember()
    
    def test_assembly_team_permission(self):
        """Test that only assembly team members have permission"""
        # Create mock request objects
        class MockRequest:
            def __init__(self, user):
                self.user = user
                # Initialize is_authenticated based on user
                if user is None:
                    self.user = type('AnonymousUser', (), {'is_authenticated': False, 'team': None})
        
        # Test assembly team member has permission
        assembly_request = MockRequest(self.assembler)
        self.assertTrue(self.permission.has_permission(assembly_request, None))
        
        # Test wing team member does not have permission
        wing_request = MockRequest(self.wing_user)
        self.assertFalse(self.permission.has_permission(wing_request, None))
        
        # Test unauthenticated user does not have permission
        no_auth_request = MockRequest(None)
        self.assertFalse(self.permission.has_permission(no_auth_request, None))
