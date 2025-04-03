from rest_framework.routers import DefaultRouter
from .views import PartViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'parts', PartViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
