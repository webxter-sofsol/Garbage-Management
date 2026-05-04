#!/usr/bin/env python
"""
Debug script to check session and OTP status.
Run with: python debug_sessions.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gcms.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.utils import timezone
from authentication.models import OTP, User

def debug_sessions():
    """Debug session and authentication issues."""
    
    print("=== GCMS Session Debug Report ===")
    print(f"Current time: {timezone.now()}")
    print()
    
    # Check active sessions
    active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
    expired_sessions = Session.objects.filter(expire_date__lte=timezone.now())
    
    print(f"Active sessions: {active_sessions.count()}")
    print(f"Expired sessions: {expired_sessions.count()}")
    print()
    
    # Check OTPs
    valid_otps = OTP.objects.filter(is_used=False, expires_at__gt=timezone.now())
    expired_otps = OTP.objects.filter(expires_at__lte=timezone.now())
    used_otps = OTP.objects.filter(is_used=True)
    
    print(f"Valid OTPs: {valid_otps.count()}")
    print(f"Expired OTPs: {expired_otps.count()}")
    print(f"Used OTPs: {used_otps.count()}")
    print()
    
    # Check users
    total_users = User.objects.count()
    citizens = User.objects.filter(is_citizen=True).count()
    authorities = User.objects.filter(is_authority=True).count()
    staff = User.objects.filter(is_staff_member=True).count()
    users_with_password = User.objects.filter(has_password=True).count()
    
    print(f"Total users: {total_users}")
    print(f"Citizens: {citizens}")
    print(f"Authorities: {authorities}")
    print(f"Staff members: {staff}")
    print(f"Users with password: {users_with_password}")
    print()
    
    # Recent users and their login methods
    recent_users = User.objects.order_by('-created_at')[:5]
    if recent_users:
        print("Recent users and login methods:")
        for user in recent_users:
            methods = user.get_login_methods()
            print(f"  {user.email} - {', '.join(methods)} - {user.get_user_type()}")
    print()
    
    # Recent OTPs
    recent_otps = OTP.objects.order_by('-created_at')[:5]
    if recent_otps:
        print("Recent OTPs:")
        for otp in recent_otps:
            status = "VALID" if otp.is_valid() else "INVALID"
            print(f"  {otp.email} - {otp.code} - {status} - {otp.created_at}")
    
    print("\n=== End Report ===")

if __name__ == "__main__":
    debug_sessions()