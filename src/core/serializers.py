
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import ClientModel,LeadModel,DesignationModel

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model=DesignationModel
        fields=['name']

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model=ClientModel
        fields=['full_name','email','contact']

    def validate(self, attrs):
        if len(attrs['full_name'])>5:
            raise serializers.ValidationError('Fullname must be more 5 character ')

        if attrs['contact'].isDigit:
            raise serializers.ValidationError('Contact number must be digits')

        return attrs


class LeadClientSerializer(serializers.ModelSerializer):
    clients=ClientSerializer(read_only=True)
    class Meta:
        model=LeadModel
        fields=['clients','user','designation','salary','experience']


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model=LeadModel
        fields=['designation','salary','experience']

    def validate(self, attrs):
        if attrs['salary']<10000:
            raise serializers.ValidationError('Salary must be more than 10000 ')
        if attrs['experience']<2:
            raise serializers.ValidationError('Lead should have more 2 year of experience')

        return attrs
