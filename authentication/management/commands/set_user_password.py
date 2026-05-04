"""
Management command to set password for existing users.
Usage: python manage.py set_user_password user@example.com
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from getpass import getpass
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Set password for an existing user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')
        parser.add_argument(
            '--password',
            type=str,
            help='Password (if not provided, will prompt securely)'
        )

    def handle(self, *args, **options):
        """Set password for user."""
        email = options['email'].lower().strip()
        password = options.get('password')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email "{email}" does not exist.')
        
        if not password:
            password = getpass('Enter new password: ')
            confirm_password = getpass('Confirm password: ')
            
            if password != confirm_password:
                raise CommandError('Passwords do not match.')
        
        if len(password) < 8:
            raise CommandError('Password must be at least 8 characters long.')
        
        # Set password
        user.set_password(password)
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set password for user "{email}". '
                f'User can now login with both password and OTP.'
            )
        )
        
        logger.info(f"Password set for user {email} via management command")