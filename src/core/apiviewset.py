# views.py
from rest_framework.exceptions import PermissionDenied
from .base_views import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import DesignationModel, LeadModel, ClientModel
from .serializers import (
    DesignationSerializer,
    LeadSerializer,
    ClientSerializer,
    LeadClientSerializer
)

class DesignationListAPIView(ListCreateAPIView):
    """Designation list and create view with caching"""
    model = DesignationModel
    serializer_class = DesignationSerializer
    cache_prefix = "designations"
    cache_timeout = 3600  # 1 hour

    def get_queryset(self):
        # Using indexed field 'name' for ordering
        return DesignationModel.objects.all().order_by('name')

    def get_cache_key(self, user_id=None):
        # Designations are global, no user-specific caching
        return self.get_cache_key(self.cache_prefix, "all")

class DesignationDetailAPIView(RetrieveUpdateDestroyAPIView):
    """Designation detail view"""
    model = DesignationModel
    serializer_class = DesignationSerializer
    cache_prefix = "designation"

    def invalidate_caches(self, request, instance, deleted=False):
        cache.delete(self.get_cache_key("designations", "all"))
        cache.delete(self.get_cache_key(instance.id))

class LeadListCreateAPIView(ListCreateAPIView):
    """Lead list and create view with user-specific caching"""
    model = LeadModel
    serializer_class = LeadClientSerializer
    cache_prefix = "leads"

    def get_queryset(self):
        # Using indexed fields and select_related for optimization
        return LeadModel.objects.filter(
            user=self.request.user
        ).select_related('user').order_by('-created_at')

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    def invalidate_caches(self, request, instance):
        # Invalidate user-specific leads cache
        cache.delete(self.get_cache_key(request.user.id))
        # Invalidate any pattern-based caches if using Redis
        self.invalidate_pattern(f"user_{self.cache_prefix}_*")

class LeadDetailAPIView(RetrieveUpdateDestroyAPIView):
    """Lead detail view with ownership validation"""
    model = LeadModel
    serializer_class = LeadSerializer
    cache_prefix = "lead"

    def get_queryset(self):
        return LeadModel.objects.select_related('user')

    def get_object(self, pk):
        instance = super().get_object(pk)
        # Validate ownership
        if instance.user != self.request.user:
            raise PermissionDenied("You don't have permission to access this lead")
        return instance

    def invalidate_caches(self, request, instance, deleted=False):
        user_id = request.user.id
        cache.delete(self.get_cache_key(instance.id))
        cache.delete(self.get_cache_key("leads", user_id))

class ClientListCreateAPIView(ListCreateAPIView):
    """Client list and create view"""
    model = ClientModel
    serializer_class = ClientSerializer
    cache_prefix = "clients"

    def get_queryset(self):
        return ClientModel.objects.filter(
            manage_by=self.request.user
        ).select_related('manage_by').order_by('-created_at')

    def perform_create(self, serializer):
        return serializer.save(manage_by=self.request.user)

    def invalidate_caches(self, request, instance):
        cache.delete(self.get_cache_key(request.user.id))
        self.invalidate_pattern(f"user_{self.cache_prefix}_*")

class ClientDetailAPIView(RetrieveUpdateDestroyAPIView):
    """Client detail view with ownership validation"""
    model = ClientModel
    serializer_class = ClientSerializer
    cache_prefix = "client"

    def get_queryset(self):
        return ClientModel.objects.select_related('manage_by')

    def get_object(self, pk):
        instance = super().get_object(pk)
        if instance.manage_by != self.request.user:
            raise PermissionDenied("You don't have permission to access this client")
        return instance

    def invalidate_caches(self, request, instance, deleted=False):
        user_id = request.user.id
        cache.delete(self.get_cache_key(instance.id))
        cache.delete(self.get_cache_key("clients", user_id))

