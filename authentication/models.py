from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_authority', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email as the unique identifier.
    Supports three user types: citizen, authority, and staff_member.
    """
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text='User email address (used for login)'
    )
    is_citizen = models.BooleanField(
        default=True,
        help_text='Designates whether this user is a citizen'
    )
    is_authority = models.BooleanField(
        default=False,
        help_text='Designates whether this user is a municipal authority'
    )
    is_staff_member = models.BooleanField(
        default=False,
        help_text='Designates whether this user is a collection staff member'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user account is active'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into admin site'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_citizen']),
            models.Index(fields=['is_authority']),
            models.Index(fields=['is_staff_member']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_user_type(self):
        """Return the user type as a string."""
        if self.is_authority:
            return 'authority'
        elif self.is_staff_member:
            return 'staff_member'
        elif self.is_citizen:
            return 'citizen'
        return 'unknown'


class OTP(models.Model):
    """
    One-Time Password model for email-based authentication.
    OTPs expire after 10 minutes and are invalidated after use.
    """
    email = models.EmailField(
        max_length=255,
        db_index=True,
        help_text='Email address for which OTP was generated'
    )
    code = models.CharField(
        max_length=6,
        help_text='6-digit OTP code'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(
        db_index=True,
        help_text='Expiration timestamp (10 minutes from creation)'
    )
    is_used = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether this OTP has been used'
    )
    
    class Meta:
        db_table = 'otps'
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_used']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.email} - {self.code}"
    
    def save(self, *args, **kwargs):
        """Set expiration time to 10 minutes from creation if not set."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if OTP is valid (not used and not expired)."""
        return not self.is_used and timezone.now() < self.expires_at
    
    @staticmethod
    def generate_code():
        """Generate a random 6-digit OTP code."""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_otp(cls, email):
        """
        Create a new OTP for the given email.
        Invalidates any previous unused OTPs for the same email atomically.
        """
        from django.db import transaction

        with transaction.atomic():
            # Invalidate previous unused OTPs
            cls.objects.filter(email=email, is_used=False).update(is_used=True)

            # Create new OTP
            code = cls.generate_code()
            otp = cls.objects.create(email=email, code=code)
        return otp
    
    @classmethod
    def verify_otp(cls, email, code):
        """
        Verify OTP for the given email and code.
        Returns the OTP object if valid, None otherwise.
        Uses filter+first to safely handle duplicate OTP edge cases.
        """
        try:
            # Use filter().order_by().first() to avoid MultipleObjectsReturned
            # if duplicates somehow exist; picks the most recently created one
            otp = cls.objects.filter(
                email=email,
                code=code,
                is_used=False
            ).order_by('-created_at').first()

            if otp is None:
                return None

            if otp.is_valid():
                # Mark all matching unused OTPs as used (clean up duplicates)
                cls.objects.filter(
                    email=email,
                    code=code,
                    is_used=False
                ).update(is_used=True)
                return otp
            return None
        except Exception:
            return None
