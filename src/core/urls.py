from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apiviewset import (
    DesignationListAPIView,
    DesignationDetailAPIView,
    LeadListCreateAPIView,
    LeadDetailAPIView,
    ClientListCreateAPIView,
    ClientDetailAPIView,
)

# Using Router for better URL management
router = DefaultRouter()

urlpatterns = [
    # Designation endpoints
    path('designations/', DesignationListAPIView.as_view(), name='designation-list'),
    path('designations/<int:pk>/', DesignationDetailAPIView.as_view(), name='designation-detail'),

    # Lead endpoints
    path('leads/', LeadListCreateAPIView.as_view(), name='lead-list-create'),
    path('leads/<int:pk>/', LeadDetailAPIView.as_view(), name='lead-detail'),

    # Client endpoints
    path('clients/', ClientListCreateAPIView.as_view(), name='client-list-create'),
    path('clients/<int:pk>/', ClientDetailAPIView.as_view(), name='client-detail'),
]