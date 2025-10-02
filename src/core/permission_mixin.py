from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly

class AuthenticationBasePermissionMixin(BasePermission):
    permission_classes=[IsAuthenticated,IsAuthenticatedOrReadOnly]

