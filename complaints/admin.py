from django.contrib import admin
from .models import Complaint, ComplaintPhoto


class ComplaintPhotoInline(admin.TabularInline):
    """Inline admin for complaint photos."""
    model = ComplaintPhoto
    extra = 0
    readonly_fields = ('uploaded_at',)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    """Admin interface for Complaint model."""
    
    list_display = ('complaint_id', 'citizen', 'status', 'created_at', 'assigned_staff', 'response_time')
    list_filter = ('status', 'created_at', 'assigned_at', 'resolved_at')
    search_fields = ('complaint_id', 'citizen__email', 'description')
    readonly_fields = ('complaint_id', 'created_at', 'assigned_at', 'resolved_at', 'response_time')
    inlines = [ComplaintPhotoInline]
    
    fieldsets = (
        ('Complaint Information', {
            'fields': ('complaint_id', 'citizen', 'description', 'status')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Assignment', {
            'fields': ('assigned_staff', 'assigned_at')
        }),
        ('Resolution', {
            'fields': ('resolved_at', 'response_time')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('citizen', 'assigned_staff')


@admin.register(ComplaintPhoto)
class ComplaintPhotoAdmin(admin.ModelAdmin):
    """Admin interface for ComplaintPhoto model."""
    
    list_display = ('complaint', 'photo_type', 'uploaded_at')
    list_filter = ('photo_type', 'uploaded_at')
    search_fields = ('complaint__complaint_id',)
    readonly_fields = ('uploaded_at',)
