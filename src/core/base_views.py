# base_views.py
from django.core.cache import cache
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound
import logging

logger = logging.getLogger(__name__)

class CacheMixin:
    """Mixin for cache operations"""

    def get_cache_key(self, prefix, identifier):
        return f"{prefix}_{identifier}"

    def invalidate_pattern(self, pattern):
        """Invalidate cache keys matching pattern (requires Redis)"""
        try:
            if hasattr(cache, 'delete_pattern'):  # Redis specific
                cache.delete_pattern(pattern)
            else:
                # Fallback for other cache backends
                cache.delete(pattern)
        except Exception as e:
            logger.warning(f"Cache invalidation failed for pattern {pattern}: {str(e)}")

class BaseModelAPIView(APIView, CacheMixin):
    """Base class for model-based API views"""
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    cache_timeout = 300
    cache_prefix = None

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self, pk):
        try:
            return self.get_queryset().get(pk=pk)
        except self.model.DoesNotExist:
            raise NotFound(f"{self.model.__name__} not found")

class ListCreateAPIView(BaseModelAPIView):
    """Base class for list and create operations"""

    def get_cache_key(self, user_id=None):
        if user_id:
            return self.get_cache_key(f"user_{self.cache_prefix}", user_id)
        return self.get_cache_key(self.cache_prefix, "list")

    def get(self, request, *args, **kwargs):
        try:
            cache_key = self.get_cache_key(request.user.id)
            cached_data = cache.get(cache_key)

            if cached_data is not None:
                return Response(cached_data, status=status.HTTP_200_OK)

            queryset = self.get_queryset()
            serializer = self.serializer_class(queryset, many=True)

            # Cache the serialized data
            cache.set(cache_key, serializer.data, self.cache_timeout)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.get: {str(e)}")
            return Response(
                {"error": "Failed to fetch data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = self.serializer_class(data=request.data)
                serializer.is_valid(raise_exception=True)
                instance = self.perform_create(serializer)

                # Invalidate relevant caches
                self.invalidate_caches(request, instance)

                return Response(
                    self.serializer_class(instance).data,
                    status=status.HTTP_201_CREATED
                )

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.post: {str(e)}")
            return Response(
                {"error": "Failed to create object"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        return serializer.save()

    def invalidate_caches(self, request, instance):
        """Override in subclasses to define cache invalidation logic"""
        pass

class RetrieveUpdateDestroyAPIView(BaseModelAPIView):
    """Base class for retrieve, update, and destroy operations"""

    def get_cache_key(self, pk):
        return self.get_cache_key(self.cache_prefix, pk)

    def get(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            cache_key = self.get_cache_key(pk)
            cached_data = cache.get(cache_key)

            if cached_data is not None:
                return Response(cached_data, status=status.HTTP_200_OK)

            instance = self.get_object(pk)
            serializer = self.serializer_class(instance)

            cache.set(cache_key, serializer.data, self.cache_timeout)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except NotFound as e:
            raise e
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.get: {str(e)}")
            return Response(
                {"error": "Failed to fetch object"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object(kwargs.get('pk'))
                serializer = self.serializer_class(
                    instance,
                    data=request.data,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                updated_instance = serializer.save()

                self.invalidate_caches(request, updated_instance)

                return Response(serializer.data, status=status.HTTP_200_OK)

        except (NotFound, ValidationError) as e:
            raise e
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.put: {str(e)}")
            return Response(
                {"error": "Failed to update object"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object(kwargs.get('pk'))
                instance_id = instance.id
                user_id = request.user.id

                instance.delete()
                self.invalidate_caches(request, instance, deleted=True)

                return Response(status=status.HTTP_204_NO_CONTENT)

        except NotFound as e:
            raise e
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.delete: {str(e)}")
            return Response(
                {"error": "Failed to delete object"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def invalidate_caches(self, request, instance, deleted=False):
        """Override in subclasses to define cache invalidation logic"""
        pass