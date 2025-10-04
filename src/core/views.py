from rest_framework.exceptions import ValidationError
from rest_framework.response import  Response
from rest_framework.views import  APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly,IsAdminUser
from .models import DesignationModel,LeadModel,ClientModel
from .serializers import DesignationSerializer,LeadSerializer,ClientSerializer,LeadClientSerializer
from .permission_mixin import AuthenticationBasePermissionMixin
from django.core.cache import cache
from .tasks import send_email_task, send_welcome_email
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView

class DesignationApiView(APIView):
    permission_classes = [IsAuthenticated]  # Fixed duplicate permission

    def get(self, request):
        cache_key = 'designation_list'
        instance = cache.get(cache_key)

        if instance is None:
            # Using select_related/prefetch_related if there are foreign keys
            # Using indexed field 'name' for ordering
            instance = list(DesignationModel.objects.all().order_by('name'))
            cache.set(cache_key, instance, timeout=3600)

        serializer = DesignationSerializer(instance, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DesignationAPIViewRetrieve(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        # Using indexed primary key lookup
        try:
            return DesignationModel.objects.get(pk=pk)
        except DesignationModel.DoesNotExist:
            return None

    def get(self, *args, **kwargs):
        instance = self.get_object(kwargs['pk'])
        if not instance:
            raise ValidationError('No object exists')
        serializer = DesignationSerializer(instance=instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LeadCreateRetrieveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        cache_key = f'user_leads_{user.id}'

        instance = cache.get(cache_key)
        if instance is None:
            # Using indexed field 'user' and ordering by indexed 'created_at'
            instance = LeadModel.objects.filter(user=user).select_related(
                'user'
            ).order_by('-created_at')
            cache.set(cache_key, list(instance), timeout=300)  # 5 minutes cache

        serializer = LeadClientSerializer(instance=instance, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        try:
            serializer = LeadSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                # Invalidate user-specific lead cache
                cache.delete(f'user_leads_{request.user.id}')
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            raise ValidationError(f'Something went wrong: {str(e)}')


class LeadRetrieveUpdateDestroyed(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            # Using indexed primary key and select_related for foreign keys
            return LeadModel.objects.select_related('user').get(pk=pk)
        except LeadModel.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        cache_key = f'lead_{kwargs["pk"]}'
        instance = cache.get(cache_key)

        if not instance:
            instance = self.get_object(kwargs['pk'])
            if not instance:
                return Response(status=status.HTTP_404_NOT_FOUND)
            cache.set(cache_key, instance, timeout=300)  # Cache individual lead

        serializer = LeadSerializer(instance=instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        instance = self.get_object(kwargs['pk'])
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = LeadSerializer(instance=instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Invalidate caches
            cache.delete(f'lead_{kwargs["pk"]}')
            cache.delete(f'user_leads_{request.user.id}')
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object(kwargs['pk'])
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user_id = request.user.id
        instance.delete()
        # Invalidate caches
        cache.delete(f'lead_{kwargs["pk"]}')
        cache.delete(f'user_leads_{user_id}')
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientCreateRetrieveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        cache_key = f'user_clients_{user.id}'

        instance = cache.get(cache_key)
        if instance is None:
            # Using indexed field 'manage_by' and ordering by indexed 'created_at'
            instance = ClientModel.objects.filter(manage_by=user).select_related(
                'manage_by'
            ).order_by('-created_at')
            cache.set(cache_key, list(instance), timeout=300)

        serializer = ClientSerializer(instance=instance, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(manage_by=request.user)
            # Invalidate user-specific client cache
            cache.delete(f'user_clients_{request.user.id}')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientRetrieveUpdateDestroyed(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            # Using indexed primary key and select_related
            return ClientModel.objects.select_related('manage_by').get(pk=pk)
        except ClientModel.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        cache_key = f'client_{kwargs["pk"]}'
        instance = cache.get(cache_key)

        if not instance:
            instance = self.get_object(kwargs['pk'])
            if not instance:
                return Response(status=status.HTTP_404_NOT_FOUND)
            cache.set(cache_key, instance, timeout=300)

        serializer = ClientSerializer(instance=instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        instance = self.get_object(kwargs['pk'])
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ClientSerializer(instance=instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Invalidate caches
            cache.delete(f'client_{kwargs["pk"]}')
            cache.delete(f'user_clients_{request.user.id}')
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object(kwargs['pk'])
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user_id = request.user.id
        instance.delete()
        # Invalidate caches
        cache.delete(f'client_{kwargs["pk"]}')
        cache.delete(f'user_clients_{user_id}')
        return Response(status=status.HTTP_204_NO_CONTENT)


"""
 Simple Email service for info user : 
"""

# Simple email
@login_required
def some_view(request):
    # This will run in background
    send_email_task.delay(
        "Test Subject",
        "This is a test message",
        [f"{request.user.email}"]
    )
    return Response("Email queued!")

# Welcome email
@login_required
def register_user(request):
    # After user registration
    send_welcome_email.delay(
        user_email=f"{request.user.email}",
        username=f"{request.user.username}"
    )
    return Response("Registration complete! Welcome email sent.")
