from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.assembly.views import (
    AssemblyProcessViewSet,
    AvailablePartsView,
    CompletedAircraftViewSet,
    assembly_list_view,
    assembly_detail_view,
    aircraft_detail_view
)

router = DefaultRouter()
router.register(r'processes', AssemblyProcessViewSet, basename='assembly-process')
router.register(r'aircraft', CompletedAircraftViewSet, basename='completed-aircraft')

# Template view endpoints
template_urlpatterns = [
    path('', assembly_list_view, name='assembly_list'),
    path('detail/<int:pk>/', assembly_detail_view, name='assembly_detail'),
    path('aircraft/<int:pk>/', aircraft_detail_view, name='aircraft_detail'),
]

# API endpoints
api_urlpatterns = [
    path('api/', include(router.urls)),
    path('api/available-parts/<str:aircraft_type>/', AvailablePartsView.as_view(), name='available-parts'),
]

urlpatterns = template_urlpatterns + api_urlpatterns
