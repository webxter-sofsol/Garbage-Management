from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from .services import AuthenticationService
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_protect, name='dispatch')
class RegisterView(View):
    """View for user registration - sends OTP to email."""
    
    template_name = 'authentication/register.html'
    
    def get(self, request):
        """Display registration form."""
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name)
    
    def post(self, request):
        """Process registration - send OTP."""
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, 'Please provide an email address.')
            return render(request, self.template_name)
        
        # Generate and send OTP
        success, message = AuthenticationService.register_or_login(email)
        
        if success:
            # Store email in session for OTP verification
            request.session['pending_email'] = email
            messages.success(request, message)
            return redirect('authentication:verify_otp')
        else:
            messages.error(request, message)
            return render(request, self.template_name)


@method_decorator(csrf_protect, name='dispatch')
class VerifyOTPView(View):
    """View for OTP verification."""
    
    template_name = 'authentication/verify_otp.html'
    
    def get(self, request):
        """Display OTP verification form."""
        if request.user.is_authenticated:
            return redirect('home')
        
        # Check if email is in session
        if 'pending_email' not in request.session:
            messages.error(request, 'Please register or login first.')
            return redirect('authentication:register')
        
        context = {
            'email': request.session.get('pending_email')
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Process OTP verification."""
        email = request.session.get('pending_email')
        otp_code = request.POST.get('otp', '').strip()
        
        if not email:
            messages.error(request, 'Session expired. Please try again.')
            return redirect('authentication:register')
        
        if not otp_code:
            messages.error(request, 'Please enter the OTP code.')
            return render(request, self.template_name, {'email': email})
        
        # Verify OTP
        success, message, user = AuthenticationService.verify_and_login(email, otp_code)
        
        if success and user:
            # Log the user in
            login(request, user)
            
            # Clear pending email from session
            if 'pending_email' in request.session:
                del request.session['pending_email']
            
            messages.success(request, 'Login successful!')
            logger.info(f"User {email} logged in successfully")
            
            # Redirect based on user type
            if user.is_authority:
                return redirect('complaints:authority_dashboard')
            elif user.is_staff_member:
                return redirect('home')  # Will be 'staff:my_assignments' when implemented
            else:  # citizen
                return redirect('home')
        else:
            messages.error(request, message)
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
