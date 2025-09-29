from dataclasses import fields

from django.db import models
from django.contrib.auth.models import  AbstractBaseUser,UserManager,PermissionsMixin
from pandas.core.interchange.from_dataframe import set_nulls

# basemodel
class BaseModel(models.Model):
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True

class CustomManager(UserManager):
    def create_user(self,email,password=None,**kwargs):
        """
        Create and return a regular user with an email and password :
        """
        if not email:
            return ValueError('The Email field must be set')

        email=self.normalize_email(email)
        user=self.model(email=email,**kwargs)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser,PermissionsMixin):

    """
    custom user model for add new extra fields :
    """

    email=models.EmailField(unique=True)
    first_name=models.CharField(max_length=50,null=False,blank=False)
    last_name=models.CharField(max_length=50,null=False,blank=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    bio=models.TextField()
    profile_pic=models.ImageField(upload_to='media/lead_profile_pic',null=True,blank=True)

    """
     Here we're using email instead of username for authentication 
    """

    USERNAME_FIELDS='email'

    REQUIRED_FIELDS = ['first_name','last_name']
    object=CustomManager()

    def __str__(self):
        return f'user name : {self.first_name} {self.last_name} with email Id : {self.email}'

    """
    Applying indexing for faster searching and reduce the time complexity of read operation from O(n) to O(long(n)). 
    """
    class Meta:
        indexes=[
            models.Index(fields=['first_name','last_name']),
            models.Index(fields=['email'])
        ]


# designation model :

class DesignationModel(models.Model):
    name=models.CharField(max_length=50,db_index=True)
    def __str__(self):
        return self.name

# Lead model
class LeadModel(BaseModel):

    user=models.OneToOneField(CustomUser,null=False,blank=False,on_delete=models.SET_NULL)
    designation=models.ForeignKey(DesignationModel,on_delete=models.CASCADE,related_name='lead_designation')
    experience=models.IntegerField(default=2)
    salary=models.DecimalField(decimal_places=2,max_digits=7)
    is_active=models.BooleanField(default=True)

    def __str__(self):
        return self.designation


# Client model
class ClientModel(BaseModel):
    full_name=models.CharField(max_length=50,null=True,blank=True)
