
from rest_framework import serializers
from .models import ClientModel,LeadModel,DesignationModel

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model=DesignationModel
        fields=['name']

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model=ClientModel
        fields='__all__'


class LeadClientSerializer(serializers.ModelSerializer):
    clients=ClientSerializer(read_only=True)
    class Meta:
        model=LeadModel
        fields=['clients','user','designation','salary','experience']


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model=LeadModel
        fields=['user','designation','salary','experience']

