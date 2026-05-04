from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Registration
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register-password/', views.RegisterPasswordView.as_view(), name='register_password'),
    
    # Login options
    path('login/', views.LoginChoiceView.as_view(), name='login'),
    path('login-choice/', views.LoginChoiceView.as_view(), name='login_choice'),
    path('password-login/', views.PasswordLoginView.as_view(), name='password_login'),
    
    # OTP flow
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend_otp'),
    
    # Password management
    path('set-password/', views.SetPasswordView.as_view(), name='set_password'),
    
    # AJAX
    path('check-email/', views.CheckEmailView.as_view(), name='check_email'),
    
    # Common
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('debug-session/', views.SessionDebugView.as_view(), name='debug_session'),
]
