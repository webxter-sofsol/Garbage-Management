# GCMS Authentication System

## Overview

The GCMS authentication system supports **dual authentication methods** with **flexible registration options**:

### 🔐 **Authentication Methods**
1. **OTP (One-Time Password)** - Email-based codes (always available)
2. **Password** - Traditional email/password login (optional)

### 📝 **Registration Options**
1. **OTP Registration** - Quick setup with email verification (recommended)
2. **Password Registration** - Create account with password immediately

Users can choose their preferred registration method and switch between authentication methods anytime.

## Features

### 🚀 **Flexible Registration**
- **OTP Registration**: Email → Verify Code → Account Created
- **Password Registration**: Email → Set Password → Account Created  
- **User Choice**: Clear options presented upfront
- **Existing User Detection**: Prevents duplicate accounts

### 🔐 **Dual Authentication Support**
- **OTP Login**: Email-based 6-digit codes (no password required)
- **Password Login**: Traditional email/password authentication
- **Flexible Choice**: Users can switch between methods anytime
- **Backward Compatible**: Existing users unaffected

### 🛡️ **Security Features**
- Session regeneration on login (prevents session fixation)
- Password strength validation (minimum 8 characters)
- OTP expiration (10 minutes)
- Session timeout management (24 hours default)
- Secure password hashing (Django's built-in PBKDF2)
- Duplicate account prevention

### 👥 **User Types**
- **Citizens**: Regular users who report issues
- **Authorities**: Municipal staff who manage complaints
- **Staff Members**: Collection staff who handle pickups

## Registration & Authentication Flow

### New User Registration

#### Option 1: OTP Registration (Recommended)
```
Email Input → Choose "Email Code" → Send OTP → Verify Code → Account Created
```

#### Option 2: Password Registration
```
Email Input → Choose "Password" → Set Password → Account Created
```

### Existing User Login
```
Email Input → System Shows Available Methods → Choose Method → Login Success
```

### Available Login Methods
- **OTP**: Always available for all users
- **Password**: Available if user has set one during registration or later

## URL Structure

| URL | Purpose | Method |
|-----|---------|--------|
| `/auth/register/` | Registration method choice | GET/POST |
| `/auth/register-password/` | Password registration form | GET/POST |
| `/auth/login/` | Login method selection | GET/POST |
| `/auth/login-choice/` | Choose between OTP/password | GET/POST |
| `/auth/password-login/` | Password-based login | GET/POST |
| `/auth/verify-otp/` | OTP verification | GET/POST |
| `/auth/set-password/` | Set up password for existing account | GET/POST |
| `/auth/logout/` | User logout | GET/POST |

## Templates

### Registration Templates
- `register.html` - Registration method choice (OTP vs Password)
- `register_password.html` - Password registration form with strength meter
- `verify_otp.html` - OTP verification (with registration links)

### Login Templates  
- `login_choice.html` - Method selection interface
- `password_login.html` - Password login form
- `set_password.html` - Password setup form

### Template Features
- **Responsive Design**: Works on desktop and mobile
- **Real-time Validation**: Password strength, email format
- **User Feedback**: Clear error messages and success states
- **Accessibility**: Proper labels, keyboard navigation
- **Method Switching**: Easy links between registration/login options

## Database Schema

### User Model Fields
```python
email = EmailField(unique=True)           # Primary identifier
password = CharField(blank=True)          # Hashed password (optional)
has_password = BooleanField(default=False) # Whether password is set
prefer_otp = BooleanField(default=True)   # User preference
is_citizen = BooleanField(default=True)   # User type flags
is_authority = BooleanField(default=False)
is_staff_member = BooleanField(default=False)
```

### OTP Model
```python
email = EmailField()                      # Target email
code = CharField(max_length=6)           # 6-digit code
created_at = DateTimeField()             # Creation time
expires_at = DateTimeField()             # Expiration (10 min)
is_used = BooleanField(default=False)    # Usage status
```

## Management Commands

### Set User Password
```bash
# Interactive password setting
python manage.py set_user_password user@example.com

# With password argument (not recommended for production)
python manage.py set_user_password user@example.com --password mypassword
```

### Clean Up Sessions
```bash
# Remove expired sessions and OTPs
python manage.py cleanup_sessions
```

## Debug Tools

### Debug Script
```bash
# Check authentication system status
python debug_sessions.py
```

### Debug Endpoint (Development Only)
```
GET /auth/debug-session/
```
Returns JSON with current session information.

## Configuration

### Settings (gcms/settings.py)
```python
# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'authentication.backends.EmailBackend',    # Email/password
    'authentication.backends.OTPBackend',      # OTP authentication
    'django.contrib.auth.backends.ModelBackend',  # Admin fallback
]

# Custom User Model
AUTH_USER_MODEL = "authentication.User"
```

### Email Configuration
```python
# Required for OTP delivery
EMAIL_HOST = "smtp.hostinger.com"
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = "your-email@domain.com"
EMAIL_HOST_PASSWORD = "your-password"
```

## API Usage

### Check Available Login Methods
```python
from authentication.services import AuthenticationService

methods = AuthenticationService.get_login_methods("user@example.com")
# Returns: ['otp'] or ['otp', 'password']
```

### Password Authentication
```python
success, message, user = AuthenticationService.authenticate_with_password(
    "user@example.com", 
    "password123"
)
```

### OTP Authentication
```python
# Send OTP
success, message = AuthenticationService.register_or_login("user@example.com")

# Verify OTP
success, message, user = AuthenticationService.verify_and_login(
    "user@example.com", 
    "123456"
)
```

## Security Considerations

### Password Requirements
- Minimum 8 characters
- Must contain letters and numbers
- Stored using Django's PBKDF2 hashing

### OTP Security
- 6-digit random codes
- 10-minute expiration
- Single-use only
- Previous codes invalidated on new generation

### Session Security
- Session ID regeneration on login
- 24-hour timeout (configurable)
- Secure cookies in production
- CSRF protection on all forms

## Troubleshooting

### Common Issues

**"Session Expired" Error**
- Check session timeout settings
- Verify session backend configuration
- Clear browser cookies and try again

**OTP Not Received**
- Check email configuration in settings
- Verify SMTP credentials
- Check spam/junk folder
- Use password login as alternative

**Password Login Not Available**
- User must set password first via `/auth/set-password/`
- Or use management command: `python manage.py set_user_password email@example.com`

### Debug Steps
1. Run `python debug_sessions.py` to check system status
2. Check error logs in `logs/error.log`
3. Verify email configuration
4. Test with debug endpoint `/auth/debug-session/`

## Migration Guide

### From OTP-Only to Dual Authentication

Existing users will continue to work with OTP authentication. To enable password login:

1. **For Individual Users**: Direct them to set password via the UI
2. **For Bulk Users**: Use management command or admin interface
3. **For New Users**: They can set password during registration flow

### Backward Compatibility
- All existing OTP functionality remains unchanged
- Existing users can continue using OTP exclusively
- No breaking changes to existing authentication flow

## Best Practices

### For Users
- Use password login for frequent access (faster)
- Use OTP login when accessing from new devices
- Set a strong password with mixed characters
- Keep email account secure (used for OTP delivery)

### For Administrators
- Monitor failed login attempts in logs
- Regularly clean up expired sessions and OTPs
- Ensure email delivery is working properly
- Consider implementing rate limiting for production

### For Developers
- Always use HTTPS in production
- Implement proper error handling
- Log authentication events for security monitoring
- Test both authentication methods thoroughly