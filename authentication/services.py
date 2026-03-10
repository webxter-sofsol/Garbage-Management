"""
Authentication services for OTP generation and email sending.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import OTP, User
import logging

logger = logging.getLogger(__name__)


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
        Send OTP code via email.
        
        Args:
            email (str): Recipient email address
            code (str): 6-digit OTP code
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            subject = 'Your GCMS Login Code'
            
            # Create HTML message
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
            
            # Create plain text version
            plain_message = f"""
            Garbage Collection Management System
            
            Your one-time password (OTP) for login is: {code}
            
            This code will expire in 10 minutes.
            
            If you didn't request this code, please ignore this email.
            """
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending OTP email to {email}: {str(e)}")
            return False
    
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
            
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'is_citizen': True}
            )
            
            if created:
                logger.info(f"New user created: {email}")
            
            return True, "OTP verified successfully", user
            
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
