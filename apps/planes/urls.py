from rest_framework.routers import DefaultRouter
from .views import AssembleAircraftView
from django.urls import path, include

urlpatterns = [
    path('assemble/', AssembleAircraftView.as_view(), name='assemble-aircraft'),
]
