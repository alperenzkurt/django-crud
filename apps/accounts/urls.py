from django.urls import path, include
from .views import login_page, logout_view, profile_view, edit_profile
from .views import (
    user_list, create_user, edit_user, delete_user
)

urlpatterns = [
    path('login/', login_page, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
]

urlpatterns += [
    path('admin/users/', user_list, name='user_list'),
    path('admin/users/create/', create_user, name='create_user'),
    path('admin/users/<int:user_id>/edit/', edit_user, name='edit_user'),
    path('admin/users/<int:user_id>/delete/', delete_user, name='delete_user'),
]