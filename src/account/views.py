from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer,LoginSerializer

class RegisterAPiView(APIView):
    permission_classes = [AllowAny]

    def post(self,request,*args,**kwargs):
        serializer=RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.save()

        token=RefreshToken.for_user(user)

        return Response(
            {
                'refresh':str(token),
                'access_token':str(token.access_token)
            }
        )

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self,request,*args,**kwargs):
        serializer=LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.validated_data['user']

        token=RefreshToken.for_user(user)

        return Response(
            {
                'refresh':str(token),
                'access_token':str(token.access_token)
            }
        )