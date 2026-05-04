"""
Authentication services for OTP generation and email sending.
"""
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP, User
import logging
import threading

logger = logging.getLogger(__name__)


def _send_mail_async(subject, plain_message, from_email, recipient_list, html_message):
    """Send email in a background thread so the request is never blocked."""
    def _send():
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=True,   # background thread — log errors, don't raise
            )
            logger.info(f"OTP email sent to {recipient_list[0]}")
        except Exception as e:
            logger.error(f"Background email send failed to {recipient_list[0]}: {e}")

    t = threading.Thread(target=_send, daemon=True)
    t.start()


class OTPService:
    """Service class for OTP operations."""
    
    @staticmethod
    def generate_and_send_otp(email):
        """
        Generate OTP for email and send it via email.
        Invalidates any previous unused OTPs for the same email.
        
        Args:
            email (str): Email address to send OTP to
            
        Returns:
            tuple: (success: bool, message: str, otp: OTP or None)
        """
        try:
            # Create new OTP (this also invalidates previous ones)
            otp = OTP.create_otp(email)
            
            # Send email
            success = OTPService.send_otp_email(email, otp.code)
            
            if success:
                logger.info(f"OTP generated and sent successfully to {email}")
                return True, "OTP sent successfully", otp
            else:
                logger.error(f"Failed to send OTP email to {email}")
                return False, "Failed to send OTP email", None
                
        except Exception as e:
            logger.error(f"Error generating OTP for {email}: {str(e)}")
            return False, f"Error generating OTP: {str(e)}", None
    
    @staticmethod
    def send_otp_email(email, code):
        """
        Send OTP code via email (non-blocking — dispatched to a background thread).

        Returns True immediately after dispatching; actual delivery is async.
        """
        subject = 'Your GCMS Login Code'

        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #198754;">Garbage Collection Management System</h2>
                    <p>Your one-time password (OTP) for login is:</p>
                    <div style="background-color: #fff; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                        <h1 style="color: #198754; letter-spacing: 5px; margin: 0;">{code}</h1>
                    </div>
                    <p>This code will expire in <strong>10 minutes</strong>.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
                    <p style="color: #6c757d; font-size: 12px;">
                        This is an automated message from GCMS. Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """

        plain_message = (
            f"Garbage Collection Management System\n\n"
            f"Your OTP for login is: {code}\n\n"
            f"This code will expire in 10 minutes.\n"
            f"If you didn't request this, please ignore this email."
        )

        _send_mail_async(
            subject=subject,
            plain_message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
        )
        return True  # always return True — delivery is async
    
    @staticmethod
    def verify_otp(email, code):
        """
        Verify OTP code for given email.
        
        Args:
            email (str): Email address
            code (str): 6-digit OTP code
            
        Returns:
            tuple: (success: bool, message: str, user: User or None)
        """
        try:
            # Verify OTP
            otp = OTP.verify_otp(email, code)
            
            if otp is None:
                return False, "Invalid or expired OTP", None
            
            # Use OTP authentication backend
            from django.contrib.auth import authenticate
            user = authenticate(email=email, otp_verified=True)
            
            if user:
                return True, "OTP verified successfully", user
            else:
                return False, "Authentication failed", None
            
        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {str(e)}")
            return False, f"Error verifying OTP: {str(e)}", None
    
    @staticmethod
    def invalidate_user_otps(email):
        """
        Invalidate all unused OTPs for a user.
        
        Args:
            email (str): Email address
        """
        try:
            OTP.objects.filter(email=email, is_used=False).update(is_used=True)
            logger.info(f"Invalidated all OTPs for {email}")
        except Exception as e:
            logger.error(f"Error invalidating OTPs for {email}: {str(e)}")


class AuthenticationService:
    """Service class for authentication operations."""
    
    @staticmethod
    def register_or_login(email):
        """
        Register new user or initiate login for existing user.
        Generates and sends OTP.
        
        Args:
            email (str): Email address
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Validate email format
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            
            try:
                validate_email(email)
            except ValidationError:
                return False, "Invalid email format"
            
            # Generate and send OTP
            success, message, otp = OTPService.generate_and_send_otp(email)
            
            if success:
                return True, "OTP sent to your email. Please check your inbox."
            else:
                return False, message
                
        except Exception as e:
            logger.error(f"Error in register_or_login for {email}: {str(e)}")
            return False, "An error occurred. Please try again."
    
    @staticmethod
    def verify_and_login(email, code):
        """
        Verify OTP and authenticate user.
        
        Args:
            email (str): Email address
            code (str): 6-digit OTP code
            
        Returns:
            tuple: (success: bool, message: str, user: User or None)
        """
        return OTPService.verify_otp(email, code)
    
    @staticmethod
    def authenticate_with_password(email, password):
        """
        Authenticate user with email and password.
        
        Args:
            email (str): Email address
            password (str): Password
            
        Returns:
            tuple: (success: bool, message: str, user: User or None)
        """
        try:
            from django.contrib.auth import authenticate
            
            # Validate email format
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            
            try:
                validate_email(email)
            except ValidationError:
                return False, "Invalid email format", None
            
            # Check if user exists and has password
            try:
                user = User.objects.get(email=email)
                if not user.has_password:
                    return False, "No password set for this account. Please use OTP login.", None
            except User.DoesNotExist:
                return False, "No account found with this email address.", None
            
            # Authenticate
            authenticated_user = authenticate(username=email, password=password)
            if authenticated_user:
                return True, "Login successful", authenticated_user
            else:
                return False, "Invalid email or password", None
                
        except Exception as e:
            logger.error(f"Error in password authentication for {email}: {str(e)}")
            return False, "An error occurred. Please try again.", None
    
    @staticmethod
    def get_login_methods(email):
        """
        Get available login methods for a user.
        
        Args:
            email (str): Email address
            
        Returns:
            list: Available login methods ['otp', 'password']
        """
        try:
            user = User.objects.get(email=email)
            return user.get_login_methods()
        except User.DoesNotExist:
            return ['otp']  # New users can only use OTP initially
