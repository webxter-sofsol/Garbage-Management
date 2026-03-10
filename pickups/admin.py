from django.contrib import admin
from .models import PickupRequest


@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    """Admin interface for PickupRequest model."""
    
    list_display = ('request_id', 'citizen', 'waste_type', 'preferred_date', 'status', 'created_at')
    list_filter = ('status', 'waste_type', 'preferred_date', 'created_at')
    search_fields = ('request_id', 'citizen__email', 'address')
    readonly_fields = ('request_id', 'created_at', 'completed_at')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('request_id', 'citizen', 'waste_type', 'status')
        }),
        ('Pickup Details', {
            'fields': ('preferred_date', 'preferred_time', 'scheduled_date', 'notes')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'address')
        }),
        ('Assignment', {
            'fields': ('assigned_staff',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('citizen', 'assigned_staff')
