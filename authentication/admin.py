from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = ('email', 'is_citizen', 'is_authority', 'is_staff_member', 'is_active', 'created_at')
    list_filter = ('is_citizen', 'is_authority', 'is_staff_member', 'is_active', 'created_at')
    search_fields = ('email',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('User Type', {'fields': ('is_citizen', 'is_authority', 'is_staff_member')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_citizen', 'is_authority', 'is_staff_member'),
        }),
    )
    
    readonly_fields = ('created_at', 'last_login')


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """Admin interface for OTP model."""
    
    list_display = ('email', 'code', 'created_at', 'expires_at', 'is_used', 'is_valid_display')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'code')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'expires_at')
    
    def is_valid_display(self, obj):
        """Display whether OTP is currently valid."""
        return obj.is_valid()
    is_valid_display.short_description = 'Valid'
    is_valid_display.boolean = True
