from django.contrib import admin
from .models import BinLocation


@admin.register(BinLocation)
class BinLocationAdmin(admin.ModelAdmin):
    list_display = ['bin_id', 'bin_type', 'address', 'is_active', 'created_at']
    list_filter = ['bin_type', 'is_active']
    search_fields = ['bin_id', 'address']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
