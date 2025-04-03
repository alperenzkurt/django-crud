from django import forms
from django.contrib.auth.forms import UserChangeForm
from .models import User
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileUpdateForm(UserChangeForm):
    password = None  # Şifre alanını kaldır (istersen ayrı sayfa yaparız)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')  # takım yok burada

class AdminUserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'team', 'password']

class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'team']
