from rest_framework import serializers
from .models import User, Team
from django.contrib.auth import authenticate

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    team = TeamSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'team']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Hatalı giriş bilgileri.")
