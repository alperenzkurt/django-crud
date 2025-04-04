from rest_framework.routers import DefaultRouter
from .views import PartViewSet, part_management
from django.urls import path, include

router = DefaultRouter()
router.register(r'parts', PartViewSet, basename='part')

urlpatterns = [
    path('', part_management, name='part_management'),
    path('api/', include(router.urls)),
]
