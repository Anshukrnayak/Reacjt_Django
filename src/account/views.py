from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class RegisterAPiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    },
                    'refresh_token': str(refresh),
                    'access_token': str(refresh.access_token)
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response(
                {'error': 'Registration failed'},
                status=status.HTTP_400_BAD_REQUEST
            )

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    },
                    'refresh_token': str(refresh),
                    'access_token': str(refresh.access_token)
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh_token')

            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)

            # Verify the token belongs to the current user
            token_user_id = token.get('user_id')
            if token_user_id != request.user.id:
                return Response(
                    {'error': 'Invalid token for user'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token.blacklist()

            # Also blacklist the access token if it exists in outstanding tokens
            access_token = request.auth
            if access_token:
                try:
                    OutstandingToken.objects.filter(token=str(access_token)).delete()
                except Exception:
                    pass

            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {'error': 'Invalid token or logout failed'},
                status=status.HTTP_400_BAD_REQUEST
            )

class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            tokens = OutstandingToken.objects.filter(user_id=request.user.id)
            blacklisted_count = 0

            for token in tokens:
                # Use get_or_create to avoid duplicates
                blacklisted_token, created = BlacklistedToken.objects.get_or_create(token=token)
                if created:
                    blacklisted_count += 1

            return Response(
                {'message': f'Successfully logged out from all devices. {blacklisted_count} tokens blacklisted.'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Logout all error: {str(e)}")
            return Response(
                {'error': 'Logout from all devices failed'},
                status=status.HTTP_400_BAD_REQUEST
            )