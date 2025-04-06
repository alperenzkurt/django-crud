from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User, Team
from rest_framework.test import APITestCase
from rest_framework import status

# Create your tests here.

class TeamModelTests(TestCase):
    """Tests for the Team model"""
    
    def setUp(self):
        self.wing_team = Team.objects.create(name='Wing Team', team_type='wing')
        self.assembly_team = Team.objects.create(name='Assembly Team', team_type='assembly')
    
    """Test string representation of Team objects"""
    def test_team_str_representation(self):
        self.assertEqual(str(self.wing_team), 'Wing Team')
    
    """Test teams can only produce their assigned part types"""
    def test_team_can_produce_part(self):
        # Wing team can produce wing parts
        self.assertTrue(self.wing_team.can_produce_part('wing'))
        
        # Wing team cannot produce other parts
        self.assertFalse(self.wing_team.can_produce_part('body'))
        self.assertFalse(self.wing_team.can_produce_part('tail'))
        self.assertFalse(self.wing_team.can_produce_part('avionics'))
        
        # Assembly team cannot produce parts
        self.assertFalse(self.assembly_team.can_produce_part('wing'))
        self.assertFalse(self.assembly_team.can_produce_part('body'))


class UserModelTests(TestCase):
    """Tests for the User model"""
    
    def setUp(self):
        self.team = Team.objects.create(name='Wing Team', team_type='wing')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword',
            team=self.team
        )
    
    """Test string representation of User objects"""
    def test_user_str_representation(self):
        self.assertEqual(str(self.user), 'testuser')
    
    """Test relationship between User and Team models"""
    def test_user_team_relationship(self):
        self.assertEqual(self.user.team, self.team)
        self.assertEqual(self.team.user_set.first(), self.user)


class LoginViewTests(TestCase):
    """Tests for the login view"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
    
    """Test that login page loads successfully"""
    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
    
    """Test successful login redirects to home"""
    def test_successful_login(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpassword'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
    
    """Test invalid credentials shows error message"""
    def test_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)


class UserAPITests(TestCase):
    """Tests for User API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.team = Team.objects.create(name='Wing Team', team_type='wing')
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpassword',
            team=self.team
        )
    
    """Test login API endpoint"""
    def test_user_login_api(self):
        url = reverse('login')
        data = {'username': 'admin', 'password': 'adminpassword'}
        response = self.client.post(url, data)
        
        # Check successful login response
        self.assertEqual(response.status_code, 302)  # Redirect after login
