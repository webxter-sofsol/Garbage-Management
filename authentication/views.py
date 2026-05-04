from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .services import AuthenticationService
from .models import User
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_protect, name='dispatch')
class RegisterView(View):
    """View for user registration - choose between OTP and password registration."""
    
    template_name = 'authentication/register.html'
    
    def get(self, request):
        """Display registration form."""
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name)
    
    def post(self, request):
        """Process registration method choice."""
        email = request.POST.get('email', '').strip().lower()
        method = request.POST.get('method', '')
        
        if not email:
            messages.error(request, 'Please provide an email address.')
            return render(request, self.template_name)
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email format.')
            return render(request, self.template_name, {'email': email})
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists. Please sign in instead.')
            return redirect(f'/auth/login-choice/?email={email}')
        
        if method == 'otp':
            # OTP registration flow
            success, message = AuthenticationService.register_or_login(email)
            if success:
                request.session['pending_email'] = email
                # Do NOT call set_expiry here — let the global SESSION_COOKIE_AGE (24h) apply
                messages.success(request, message)
                logger.info(f"OTP registration initiated for {email}")
                return redirect('authentication:verify_otp')
            else:
                messages.error(request, message)
                logger.error(f"Failed to send OTP for registration to {email}: {message}")
                return render(request, self.template_name, {'email': email})
        
        elif method == 'password':
            # Password registration flow
            return redirect(f'/auth/register-password/?email={email}')
        
        else:
            messages.error(request, 'Please select a registration method.')
            return render(request, self.template_name, {'email': email})


@method_decorator(csrf_protect, name='dispatch')
class RegisterPasswordView(View):
    """View for password-based registration."""
    
    template_name = 'authentication/register_password.html'
    
    def get(self, request):
        """Display password registration form."""
        if request.user.is_authenticated:
            return redirect('home')
        
        email = request.GET.get('email', '')
        if not email:
            messages.error(request, 'Please start from the registration page.')
            return redirect('authentication:register')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists. Please sign in instead.')
            return redirect(f'/auth/login-choice/?email={email}')
        
        context = {'email': email}
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Process password registration."""
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not email or not password or not confirm_password:
            messages.error(request, 'Please fill in all fields.')
            return render(request, self.template_name, {'email': email})
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email format.')
            return render(request, self.template_name, {'email': email})
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists. Please sign in instead.')
            return redirect(f'/auth/login-choice/?email={email}')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, self.template_name, {'email': email})
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, self.template_name, {'email': email})
        
        # Create user with password
        try:
            user = User.objects.create(
                email=email,
                is_citizen=True
            )
            user.set_password(password)
            user.save()
            
            # login() internally calls cycle_key() — do NOT call it again
            login(request, user, backend='authentication.backends.EmailBackend')
            
            messages.success(request, 'Account created successfully! Welcome to GCMS.')
            logger.info(f"New user registered with password: {email}")
            
            # Redirect based on user type
            if user.is_authority:
                return redirect('admin_dashboard')
            elif user.is_staff_member:
                return redirect('staff:my_assignments')
            else:  # citizen
                return redirect('home')
                
        except Exception as e:
            logger.error(f"Error creating user {email}: {str(e)}")
            messages.error(request, 'An error occurred while creating your account. Please try again.')
            return render(request, self.template_name, {'email': email})


@method_decorator(csrf_protect, name='dispatch')
class VerifyOTPView(View):
    """View for OTP verification."""
    
    template_name = 'authentication/verify_otp.html'
    
    def get(self, request):
        """Display OTP verification form."""
        if request.user.is_authenticated:
            return redirect('home')
        
        email = request.session.get('pending_email')
        
        if not email:
            messages.error(request, 'Session expired. Please register or login first.')
            return redirect('authentication:register')
        
        return render(request, self.template_name, {'email': email})
    
    def post(self, request):
        """Process OTP verification."""
        email = request.session.get('pending_email')
        otp_code = request.POST.get('otp', '').strip()
        
        if not email:
            messages.error(request, 'Session expired. Please register/login again.')
            logger.warning("OTP verification attempted without pending_email in session")
            return redirect('authentication:register')
        
        if not otp_code:
            messages.error(request, 'Please enter the OTP code.')
            return render(request, self.template_name, {'email': email})
        
        # Verify OTP
        success, message, user = AuthenticationService.verify_and_login(email, otp_code)
        
        if success and user:
            # login() internally calls cycle_key() in Django 4+ — do NOT call it again
            login(request, user, backend='authentication.backends.OTPBackend')
            
            # Clear pending email from session
            request.session.pop('pending_email', None)
            
            messages.success(request, 'Login successful!')
            logger.info(f"User {email} logged in successfully")
            
            # Redirect based on user type (authority takes priority)
            if user.is_authority:
                return redirect('admin_dashboard')
            elif user.is_staff_member:
                return redirect('staff:my_assignments')
            else:  # citizen
                return redirect('home')
        else:
            messages.error(request, message)
            logger.warning(f"OTP verification failed for {email}: {message}")
            return render(request, self.template_name, {'email': email})


@method_decorator(csrf_protect, name='dispatch')
class ResendOTPView(View):
    """View for resending OTP."""
    
    def post(self, request):
        """Resend OTP to the email in session."""
        email = request.session.get('pending_email')
        
        if not email:
            messages.error(request, 'Session expired. Please try again.')
            return redirect('authentication:register')
        
        # Generate and send new OTP
        success, message = AuthenticationService.register_or_login(email)
        
        if success:
            messages.success(request, 'New OTP sent to your email.')
        else:
            messages.error(request, message)
        
        return redirect('authentication:verify_otp')


class LogoutView(View):
    """View for user logout."""
    
    def get(self, request):
        """Log out the user."""
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('home')
    
    def post(self, request):
        """Log out the user (POST method)."""
        return self.get(request)


class HomeView(View):
    """Home page view."""
    
    template_name = 'home.html'
    
    def get(self, request):
        """Display home page."""
        return render(request, self.template_name)


class SessionDebugView(View):
    """Debug view to check session status (only in DEBUG mode)."""
    
    def get(self, request):
        """Display session debug information."""
        from django.conf import settings
        from django.http import JsonResponse
        
        if not settings.DEBUG:
            return JsonResponse({'error': 'Debug mode only'}, status=403)
        
        session_data = {
            'session_key': request.session.session_key,
            'session_data': dict(request.session),
            'is_authenticated': request.user.is_authenticated,
            'user_email': getattr(request.user, 'email', None),
            'session_age': getattr(request.session, 'get_expiry_age', lambda: None)(),
            'session_expiry_date': getattr(request.session, 'get_expiry_date', lambda: None)(),
        }
        
        return JsonResponse(session_data, indent=2)


@method_decorator(csrf_protect, name='dispatch')
class PasswordLoginView(View):
    """View for password-based login."""
    
    template_name = 'authentication/password_login.html'
    
    def get(self, request):
        """Display password login form."""
        if request.user.is_authenticated:
            return redirect('home')
        email = request.GET.get('email', '')
        return render(request, self.template_name, {'email': email})
    
    def post(self, request):
        """Process password login."""
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, self.template_name, {'email': email})
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email format.')
            return render(request, self.template_name, {'email': email})
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            if not user.has_password:
                messages.error(request, 
                    'No password set for this account. Please use OTP login or set a password first.')
                return render(request, self.template_name, {'email': email})
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return render(request, self.template_name, {'email': email})
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            # login() calls cycle_key() internally — do NOT call it again
            
            messages.success(request, 'Login successful!')
            logger.info(f"User {email} logged in with password")
            
            # Redirect based on user type
            if user.is_authority:
                return redirect('admin_dashboard')
            elif user.is_staff_member:
                return redirect('staff:my_assignments')
            else:  # citizen
                return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            logger.warning(f"Failed password login attempt for {email}")
            return render(request, self.template_name, {'email': email})


@method_decorator(csrf_protect, name='dispatch')
class SetPasswordView(View):
    """View for setting/changing password — works for both logged-in and unauthenticated users."""
    
    template_name = 'authentication/set_password.html'
    
    def get(self, request):
        """Display set password form."""
        # Logged-in users can set password directly
        if request.user.is_authenticated:
            context = {
                'email': request.user.email,
                'is_change': request.user.has_password,  # True = changing, False = setting new
            }
            return render(request, self.template_name, context)
        
        # Unauthenticated: email must come from session or query string
        email = request.session.get('pending_email') or request.GET.get('email')
        if not email:
            messages.error(request, 'Please start from login page.')
            return redirect('authentication:register')
        
        context = {'email': email, 'is_change': False}
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Process password setting."""
        # Logged-in users: get email from the authenticated user, not POST
        if request.user.is_authenticated:
            email = request.user.email
            user = request.user
        else:
            email = request.POST.get('email', '').strip().lower()
            user = None
        
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        is_change = request.user.is_authenticated and request.user.has_password
        
        if not password or not confirm_password:
            messages.error(request, 'Please fill in all fields.')
            return render(request, self.template_name, {'email': email, 'is_change': is_change})
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, self.template_name, {'email': email, 'is_change': is_change})
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, self.template_name, {'email': email, 'is_change': is_change})
        
        # Get user if not already set (unauthenticated flow)
        if user is None:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'is_citizen': True}
            )
        
        # Set password
        user.set_password(password)
        user.save()
        
        if request.user.is_authenticated:
            # Already logged in — just confirm and stay
            messages.success(request, 'Password updated successfully! You can now use it to sign in.')
            logger.info(f"Password {'changed' if is_change else 'set'} for logged-in user {email}")
            # Redirect back to wherever they came from
            next_url = request.GET.get('next') or request.POST.get('next', '')
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            # Log user in after setting password
            login(request, user, backend='authentication.backends.EmailBackend')
            # login() calls cycle_key() internally — do NOT call it again
            request.session.pop('pending_email', None)
            messages.success(request, 'Password set successfully! You are now logged in.')
            logger.info(f"Password set for user {email}")
            if user.is_authority:
                return redirect('admin_dashboard')
            elif user.is_staff_member:
                return redirect('staff:my_assignments')
            else:
                return redirect('home')


@method_decorator(csrf_protect, name='dispatch')
class LoginChoiceView(View):
    """View to choose between OTP and password login."""
    
    template_name = 'authentication/login_choice.html'
    
    def get(self, request):
        """Display login method choice."""
        if request.user.is_authenticated:
            return redirect('home')
        
        email = request.GET.get('email', '').strip().lower()
        context = {'email': email, 'has_password': False}
        
        if email:
            try:
                validate_email(email)
                try:
                    user = User.objects.get(email=email)
                    context['has_password'] = user.has_password
                except User.DoesNotExist:
                    context['has_password'] = False
            except ValidationError:
                messages.error(request, 'Invalid email format.')
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Process login method choice."""
        email = request.POST.get('email', '').strip().lower()
        method = request.POST.get('method', '')
        
        if not email:
            messages.error(request, 'Please provide an email address.')
            return render(request, self.template_name, {'has_password': False})
        
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email format.')
            return render(request, self.template_name, {'email': email, 'has_password': False})
        
        if method == 'password':
            return redirect(f'/auth/password-login/?email={email}')
        elif method == 'otp':
            # Store email and redirect to OTP flow
            request.session['pending_email'] = email
            # Do NOT call set_expiry — let the global SESSION_COOKIE_AGE (24h) apply
            
            # Generate and send OTP
            success, message = AuthenticationService.register_or_login(email)
            if success:
                messages.success(request, message)
                return redirect('authentication:verify_otp')
            else:
                messages.error(request, message)
                # Re-populate has_password for re-render
                has_password = False
                try:
                    user = User.objects.get(email=email)
                    has_password = user.has_password
                except User.DoesNotExist:
                    pass
                return render(request, self.template_name, {'email': email, 'has_password': has_password})
        else:
            messages.error(request, 'Please select a login method.')
            has_password = False
            try:
                user = User.objects.get(email=email)
                has_password = user.has_password
            except User.DoesNotExist:
                pass
            return render(request, self.template_name, {'email': email, 'has_password': has_password})


class CheckEmailView(View):
    """AJAX endpoint — returns login methods available for a given email."""
    
    def get(self, request):
        from django.http import JsonResponse
        email = request.GET.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({'has_password': False, 'user_exists': False})
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'has_password': False, 'user_exists': False})
        
        try:
            user = User.objects.get(email=email)
            return JsonResponse({
                'has_password': user.has_password,
                'user_exists': True,
            })
        except User.DoesNotExist:
            return JsonResponse({'has_password': False, 'user_exists': False})
