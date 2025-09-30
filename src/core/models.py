from dataclasses import fields
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MinLengthValidator

# BaseModel
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CustomManager(UserManager):
    def create_user(self, email, password=None, **kwargs):
        """
        Create and return a regular user with an email and password
        """
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
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

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for adding new extra fields
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, null=False, blank=False)
    last_name = models.CharField(max_length=50, null=False, blank=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    bio = models.TextField(blank=True)  # Added blank=True for optional field
    profile_pic = models.ImageField(upload_to='media/lead_profile_pic', null=True, blank=True)

    # Fixed: USERNAME_FIELD (not FIELDS) and should be a string
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    # Fixed: objects (not object)
    objects = CustomManager()

    def clean(self):
        super().clean()  # Call parent clean method
        if self.first_name and self.last_name and self.first_name == self.last_name:
            raise ValidationError(f'{self.first_name} and {self.last_name} should not be the same')

    def __str__(self):
        return f'user name: {self.first_name} {self.last_name} with email: {self.email}'

    """
    Applying indexing for faster searching
    """
    class Meta:
        indexes = [
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['email'])
        ]

# Designation Model
class DesignationModel(models.Model):
    name = models.CharField(
        max_length=50,
        db_index=True,
        null=False,
        blank=False,
        unique=True
    )

    def clean(self):
        if len(self.name) < 5:
            raise ValidationError(f'Length of {self.name} should be more than 5 characters')

    def __str__(self):
        return self.name

# Lead Model
class LeadModel(BaseModel):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,  # Changed from SET_NULL since null=False
        db_index=True,
        related_name='leads'
    )

    designation = models.ForeignKey(
        DesignationModel,
        on_delete=models.CASCADE,
        related_name='lead_designation',
        null=False,
        blank=False,
        db_index=True,
    )

    experience = models.IntegerField(
        default=2,
        null=False,
        blank=False
    )

    salary = models.DecimalField(
        decimal_places=2,
        max_digits=7,
        null=False,
        blank=False
    )

    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.experience < 2:
            raise ValidationError('Experience of lead should be more than 2 years')
        if self.salary < 25000:
            raise ValidationError(f'Salary {self.salary} of lead must be more than 25000')

    def __str__(self):
        return f"{self.user.first_name} - {self.designation.name}"  # Fixed to return string

# Client Model
class ClientModel(BaseModel):
    manage_by = models.ForeignKey(
        LeadModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients'
    )

    full_name = models.CharField(
        max_length=50,
        null=False,
        blank=False
    )

    email = models.EmailField(
        unique=True,
        null=False,
        blank=False
    )

    contact = models.CharField(max_length=20, null=True, blank=True)

    status = models.CharField(
        max_length=20,  # Added max_length
        choices=(
            ('Pending', 'Pending'),
            ('Completed', 'Completed'),
            ('Done', 'Done')
        ),
        default='Pending'  # Added default
    )

    def clean(self):
        if self.contact and (len(self.contact) != 10 or not self.contact.isdigit()):
            raise ValidationError(f'Contact number {self.contact} should be exactly 10 digits')

    def __str__(self):
        return self.full_name

    """
    Applying indexing in email and contact fields 
    """
    class Meta:
        indexes = [
            models.Index(fields=['email', 'contact']),
            models.Index(fields=['manage_by'])
        ]