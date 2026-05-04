"""
Management command to clean up expired sessions and OTPs.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.sessions.models import Session
from authentication.models import OTP
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired sessions and OTPs'

    def handle(self, *args, **options):
        """Clean up expired sessions and OTPs."""
        
        # Clean up expired sessions
        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        session_count = expired_sessions.count()
        expired_sessions.delete()
        
        # Clean up expired OTPs (older than 1 hour)
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        expired_otps = OTP.objects.filter(created_at__lt=one_hour_ago)
        otp_count = expired_otps.count()
        expired_otps.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cleaned up {session_count} expired sessions '
                f'and {otp_count} expired OTPs'
            )
        )
        
        logger.info(f"Cleaned up {session_count} sessions and {otp_count} OTPs")