from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.parts.models import Part
from apps.accounts.models import User, Team
from apps.parts.serializers import PartSerializer
from apps.parts.permissions import CanManagePart


class PartModelTests(TestCase):
    """Tests for the Part model"""
    
    def setUp(self):
        # Create teams
        self.wing_team = Team.objects.create(name='Wing Team', team_type='wing')
        self.body_team = Team.objects.create(name='Body Team', team_type='body')
        
        # Create users
        self.wing_user = User.objects.create_user(
            username='wing_user',
            email='wing@example.com',
            password='password',
            team=self.wing_team
        )
        
        self.body_user = User.objects.create_user(
            username='body_user',
            email='body@example.com',
            password='password',
            team=self.body_team
        )
        
        # Create parts
        self.wing_part = Part.objects.create(
            part_type='wing',
            aircraft_type='TB2',
            team=self.wing_team,
            creator=self.wing_user
        )
        
        self.body_part = Part.objects.create(
            part_type='body',
            aircraft_type='AKINCI',
            team=self.body_team,
            creator=self.body_user
        )
    
    """Test string representation of Part objects"""
    def test_part_str_representation(self):
        self.assertEqual(str(self.wing_part), 'Kanat - TB2 - {}'.format(self.wing_part.id))
        self.assertEqual(str(self.body_part), 'Gövde - AKINCI - {}'.format(self.body_part.id))
    
    """Test is_in_use property for parts"""
    def test_part_in_use_property(self):
        # Initially parts are not in use
        self.assertFalse(self.wing_part.is_in_use)
        self.assertFalse(self.body_part.is_in_use)
    
    """Test that a part cannot be recycled if in use"""
    def test_part_recycling_validation(self):
        # Set part as recycled and try to validate
        self.wing_part.is_recycled = True
        
        # Need to mock is_in_use property to simulate part in use
        original_is_in_use = self.wing_part.is_in_use
        try:
            type(self.wing_part).is_in_use = property(lambda self: True)
            
            # Should raise validation error because part is in use
            with self.assertRaises(ValidationError):
                self.wing_part.clean()
        finally:
            # Restore original is_in_use property
            type(self.wing_part).is_in_use = original_is_in_use


class PartAPITests(APITestCase):
    """Tests for Part API endpoints"""
    
    def setUp(self):
        # Create teams
        self.wing_team = Team.objects.create(name='Wing Team', team_type='wing')
        self.body_team = Team.objects.create(name='Body Team', team_type='body')
        
        # Create users
        self.wing_user = User.objects.create_user(
            username='wing_user',
            email='wing@example.com',
            password='password',
            team=self.wing_team
        )
        
        self.body_user = User.objects.create_user(
            username='body_user',
            email='body@example.com',
            password='password',
            team=self.body_team
        )
        
        # Create client
        self.client = APIClient()
        
        # Create API endpoints
        self.parts_list_url = reverse('part-list')
    
    """Test that users can only create parts for their team type"""
    def test_part_creation_permission(self):
        # Login as wing team user
        self.client.force_authenticate(user=self.wing_user)
        
        # Wing user creating wing part (should succeed)
        wing_part_data = {
            'part_type': 'wing',
            'aircraft_type': 'TB2'
        }
        
        response = self.client.post(self.parts_list_url, wing_part_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Wing user creating body part (should fail)
        body_part_data = {
            'part_type': 'body',
            'aircraft_type': 'TB2'
        }
        
        response = self.client.post(self.parts_list_url, body_part_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    """Test that users can only see parts for their team (except assembly team)"""
    def test_part_list_filtering(self):
        # Create some parts
        Part.objects.create(
            part_type='wing',
            aircraft_type='TB2',
            team=self.wing_team,
            creator=self.wing_user
        )
        
        Part.objects.create(
            part_type='body',
            aircraft_type='AKINCI',
            team=self.body_team,
            creator=self.body_user
        )
        
        # Login as wing team user
        self.client.force_authenticate(user=self.wing_user)
        
        # Should only see wing team parts
        response = self.client.get(self.parts_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['part_type'], 'wing')
        
        # Login as body team user
        self.client.force_authenticate(user=self.body_user)
        
        # Should only see body team parts
        response = self.client.get(self.parts_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['part_type'], 'body')
    
    """Test part recycling (deletion)"""
    def test_recycling_part(self):
        # Create a part
        part = Part.objects.create(
            part_type='wing',
            aircraft_type='TB2',
            team=self.wing_team,
            creator=self.wing_user
        )
        
        # Login as wing team user
        self.client.force_authenticate(user=self.wing_user)
        
        # Get the detail URL
        part_detail_url = reverse('part-detail', args=[part.id])
        
        # Update to recycle the part
        response = self.client.patch(part_detail_url, {'is_recycled': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the part is recycled
        part.refresh_from_db()
        self.assertTrue(part.is_recycled)


class PermissionTests(TestCase):
    """Tests for custom permissions"""
    
    def setUp(self):
        self.wing_team = Team.objects.create(name='Wing Team', team_type='wing')
        self.body_team = Team.objects.create(name='Body Team', team_type='body')
        
        self.wing_user = User.objects.create_user(
            username='wing_user',
            email='wing@example.com',
            password='password',
            team=self.wing_team
        )
        
        self.body_user = User.objects.create_user(
            username='body_user',
            email='body@example.com',
            password='password',
            team=self.body_team
        )
        
        self.permission = CanManagePart()
    
    """Test that teams can only manage their own parts"""
    def test_can_manage_part_permission(self):
        wing_part = Part.objects.create(
            part_type='wing',
            aircraft_type='TB2',
            team=self.wing_team,
            creator=self.wing_user
        )
        
        body_part = Part.objects.create(
            part_type='body',
            aircraft_type='TB2',
            team=self.body_team,
            creator=self.body_user
        )
        
        # Create mock request objects
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        class MockView:
            def get_object(self):
                return None
        
        # Test wing user can manage wing part but not body part
        wing_request = MockRequest(self.wing_user)
        self.assertTrue(self.permission.has_object_permission(wing_request, MockView(), wing_part))
        self.assertFalse(self.permission.has_object_permission(wing_request, MockView(), body_part))
