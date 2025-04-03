from django.contrib import admin

#custom
from django.contrib.auth.admin import UserAdmin
from .models import User, Team

# Register your models here.


admin.site.register(User, UserAdmin)
admin.site.register(Team)
