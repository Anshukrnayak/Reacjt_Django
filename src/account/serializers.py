
from rest_framework import serializers
from core.models import CustomUser
from django.contrib.auth import login,authenticate


class RegisterSerializer(serializers.ModelSerializer):
    password1=serializers.CharField(write_only=True)
    password2=serializers.CharField(write_only=True)

    class Meta:
        model=CustomUser
        fields=['first_name','last_name','email','bio','profile_pic','password1','password2']

    def validate(self, attrs):
        if len(attrs['passwords1'])!=len(attrs['password']) or attrs['password1']!=attrs['password2']:
            raise serializers.ValidationError('Passwords not matched please check you password ')
        if attrs['first_name']==attrs['last_name']:
            raise serializers.ValidationError('First name and last name not be the same ')

        return attrs

    def create(self, validated_data):
        password=validated_data('password1').pop()
        validated_data('password2').pop()
        user=CustomUser.objects.create_user(password=password,**validated_data)
        return user


class LoginSerializer(serializers.ModelSerializer):
    email=serializers.CharField(write_only=True)
    password=serializers.CharField(write_only=True)

    def validate(self, attrs):
        email=attrs.get('email')
        password=attrs.get('password')
        user=authenticate(email=email,password=password)

        if user is None:
            raise serializers.ValidationError('Invalid username or password')

        if not user.is_active:
            raise serializers.ValidationError('User is disabled ')

        attrs['user']=user
        return attrs