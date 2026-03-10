from django.contrib import admin
from .models import StaffMember, LocationUpdate


class LocationUpdateInline(admin.TabularInline):
    """Inline admin for location updates."""
    model = LocationUpdate
    extra = 0
    readonly_fields = ('latitude', 'longitude', 'timestamp', 'accuracy')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    """Admin interface for StaffMember model."""
    
    list_display = ('staff_id', 'name', 'phone', 'duty_status', 'is_active', 'get_active_complaints')
    list_filter = ('duty_status', 'is_active', 'created_at')
    search_fields = ('staff_id', 'name', 'phone', 'user__email')
    readonly_fields = ('staff_id', 'created_at', 'last_location_update', 'get_active_complaints')
    inlines = [LocationUpdateInline]
    
    fieldsets = (
        ('Staff Information', {
            'fields': ('staff_id', 'user', 'name', 'phone', 'is_active')
        }),
        ('Duty Status', {
            'fields': ('duty_status',)
        }),
        ('Current Location', {
            'fields': ('current_latitude', 'current_longitude', 'last_location_update')
        }),
        ('Statistics', {
            'fields': ('get_active_complaints',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def get_active_complaints(self, obj):
        """Display count of active complaints."""
        return obj.get_active_complaints_count()
    get_active_complaints.short_description = 'Active Complaints'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(LocationUpdate)
class LocationUpdateAdmin(admin.ModelAdmin):
    """Admin interface for LocationUpdate model."""
    
    list_display = ('staff_member', 'latitude', 'longitude', 'timestamp', 'accuracy')
    list_filter = ('timestamp',)
    search_fields = ('staff_member__name', 'staff_member__staff_id')
    readonly_fields = ('staff_member', 'latitude', 'longitude', 'timestamp', 'accuracy')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
