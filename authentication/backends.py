"""
Custom authentication backends for GCMS.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailBackend(BaseBackend):
    """
    Custom authentication backend that uses email as username.
    Supports both password and OTP authentication.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with email and password.
        
        Args:
            request: HTTP request object
            username: Email address (we use email as username)
            password: User password
            **kwargs: Additional keyword arguments
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if username is None or password is None:
            return None
        
        try:
            # Validate email format
            validate_email(username)
        except ValidationError:
            logger.warning(f"Invalid email format in authentication: {username}")
            return None
        
        try:
            # Get user by email
            user = User.objects.get(email=username)
            
            # Check if user has password set
            if not user.has_password:
                logger.warning(f"Password authentication attempted for user without password: {username}")
                return None
            
            # Check password
            if user.check_password(password) and self.user_can_authenticate(user):
                logger.info(f"Successful password authentication for: {username}")
                return user
            else:
                logger.warning(f"Failed password authentication for: {username}")
                return None
                
        except User.DoesNotExist:
            logger.warning(f"Authentication attempted for non-existent user: {username}")
            return None
        except Exception as e:
            logger.error(f"Error during authentication for {username}: {str(e)}")
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID.
        
        Args:
            user_id: User primary key
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def user_can_authenticate(self, user):
        """
        Check if user is allowed to authenticate.
        
        Args:
            user: User object
            
        Returns:
            bool: True if user can authenticate, False otherwise
        """
        return getattr(user, 'is_active', True)


class OTPBackend(BaseBackend):
    """
    Authentication backend for OTP-based authentication.
    This is used internally by the OTP verification process.
    """
    
    def authenticate(self, request, email=None, otp_verified=False, **kwargs):
        """
        Authenticate user after OTP verification.
        
        Args:
            request: HTTP request object
            email: User email address
            otp_verified: Whether OTP has been verified
            **kwargs: Additional keyword arguments
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if not email or not otp_verified:
            return None
        
        try:
            # Validate email format
            validate_email(email)
        except ValidationError:
            logger.warning(f"Invalid email format in OTP authentication: {email}")
            return None
        
        try:
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'is_citizen': True}
            )
            
            if created:
                logger.info(f"New user created via OTP authentication: {email}")
            
            if self.user_can_authenticate(user):
                logger.info(f"Successful OTP authentication for: {email}")
                return user
            else:
                logger.warning(f"OTP authentication failed - user cannot authenticate: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Error during OTP authentication for {email}: {str(e)}")
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID.
        
        Args:
            user_id: User primary key
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def user_can_authenticate(self, user):
        """
        Check if user is allowed to authenticate.
        
        Args:
            user: User object
            
        Returns:
            bool: True if user can authenticate, False otherwise
        """
        return getattr(user, 'is_active', True)