from django.shortcuts import render
from rest_framework.exceptions import ValidationError
from rest_framework.response import  Response
from rest_framework.views import  APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly,IsAdminUser
from .models import DesignationModel,LeadModel,ClientModel
from .serializers import DesignationSerializer,LeadSerializer,ClientSerializer


class DesignationApiView(APIView):
    permission_classes = [IsAuthenticated,IsAuthenticatedOrReadOnly]
    def get(self,request):
        instance=DesignationModel.objects.all()
        serializer=DesignationSerializer(instance=instance,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)


class DesignationAPIViewRetrieve(APIView):
    permission_classes = [IsAuthenticated,IsAuthenticatedOrReadOnly]

    def get_object(self,pk):
        try:
            return DesignationModel.objects.get(pk=pk)
        except DesignationModel.DoesNotExist:
            return None

    def get(self,*args,**kwargs):
        instance=self.get_object(kwargs['pk'])
        if not instance:
            raise ValidationError('No object exists : ')
        serializer=DesignationSerializer(instance=instance)
        return Response(serializer.data,status=status.HTTP_200_OK)


class LeadCreateRetrieveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,*args,**kwargs):
        instance=LeadModel.objects.all()
        serializer=LeadSerializer(instance=instance,many=True)
        return LeadSerializer(serializer.data,status=status.HTTP_200_OK)

    def post(self,request,*args,**kwargs):
        try:
            serializer=LeadSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=self.request.user)
                return Response(serializer.data,status=status.HTTP_201_CREATED)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        except:
            raise ValidationError('Something went wrong')

class LeadRetrieveUpdateDestroyed(APIView):
    pass 

