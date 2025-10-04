# models.py - Optimized for Scale
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.core.validators import MinValueValidator
import uuid

class PartitionedModel(models.Model):
    """Base model for partitioned tables"""
    partition_key = models.PositiveIntegerField(default=0)  # For manual sharding

    class Meta:
        abstract = True

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_at']),
        ]

class CustomManager(UserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin, PartitionedModel,BaseModel):
    """
    Optimized user model for 1M+ users
    """
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    # Normalize phone numbers for better indexing
    phone = models.CharField(max_length=15, null=True, blank=True, db_index=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    bio = models.TextField(blank=True)
    profile_pic = models.CharField(max_length=255, null=True, blank=True)  # Store path only

    # Metadata for analytics and partitioning
    signup_source = models.CharField(max_length=50, default='web')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomManager()

    def clean(self):
        super().clean()
        if self.first_name and self.last_name and self.first_name == self.last_name:
            raise ValidationError('First name and last name should not be the same')

    def save(self, *args, **kwargs):
        # Auto-calculate partition key based on email hash
        if not self.partition_key:
            self.partition_key = hash(self.email) % 10  # 10 partitions
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'

    class Meta:
        db_table = 'auth_user'  # Explicit table name
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['created_at']),
            models.Index(fields=['partition_key', 'is_active']),  # Composite index
        ]

class DesignationModel(models.Model):
    """
    Read-heavy table - optimized for frequent reads
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    hierarchy_level = models.PositiveIntegerField(default=0, db_index=True)

    # For soft deletion and archival
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'designations'
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['hierarchy_level']),
        ]

    def __str__(self):
        return self.name

class LeadModel(BaseModel, PartitionedModel):
    """
    Partitioned lead model for horizontal scaling
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='lead_profile'
    )

    designation = models.ForeignKey(
        DesignationModel,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='leads'
    )

    experience = models.PositiveIntegerField(default=2)
    salary = models.DecimalField(max_digits=10, decimal_places=2)  # Increased precision

    # Status tracking with efficient indexing
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_hold', 'On Hold'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )

    # Performance metrics
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    last_review_date = models.DateField(null=True, blank=True)

    # Archive and soft delete
    is_archived = models.BooleanField(default=False, db_index=True)

    def clean(self):
        if self.experience < 2:
            raise ValidationError('Experience should be at least 2 years')
        if self.salary < 25000:
            raise ValidationError('Salary must be at least 25000')

    def save(self, *args, **kwargs):
        # Auto-calculate partition based on user
        if not self.partition_key and self.user_id:
            self.partition_key = self.user.partition_key
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.designation.name}"

    class Meta:
        db_table = 'leads'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['designation', 'status']),
            models.Index(fields=['salary']),
            models.Index(fields=['created_at', 'status']),
            models.Index(fields=['partition_key', 'is_archived']),
        ]

class ClientModel(BaseModel, PartitionedModel):
    """
    High-volume client model with partitioning
    """
    manage_by = models.ForeignKey(
        LeadModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name='managed_clients'
    )

    full_name = models.CharField(max_length=100, db_index=True)  # Increased length
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20, null=True, blank=True, db_index=True)

    # Client classification
    client_tier = models.CharField(
        max_length=20,
        choices=[
            ('premium', 'Premium'),
            ('standard', 'Standard'),
            ('basic', 'Basic'),
        ],
        default='standard',
        db_index=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending',
        db_index=True
    )

    # Financial data
    lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    last_purchase_date = models.DateTimeField(null=True, blank=True)

    # Geographic data for regional partitioning
    country_code = models.CharField(max_length=3, default='US', db_index=True)
    timezone = models.CharField(max_length=50, default='UTC')

    def clean(self):
        if self.phone and (len(self.phone) < 10 or not self.phone.replace('+', '').isdigit()):
            raise ValidationError('Phone number must be valid')

    def save(self, *args, **kwargs):
        # Auto-calculate partition based on country or lead
        if not self.partition_key:
            if self.manage_by:
                self.partition_key = self.manage_by.partition_key
            else:
                self.partition_key = hash(self.email) % 10
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    class Meta:
        db_table = 'clients'
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['manage_by', 'status']),
            models.Index(fields=['client_tier', 'status']),
            models.Index(fields=['country_code', 'created_at']),
            models.Index(fields=['partition_key', 'status']),
        ]
        unique_together = ['email', 'partition_key']  # Unique within partition

        