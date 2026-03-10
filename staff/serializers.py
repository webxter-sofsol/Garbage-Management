from rest_framework import serializers
from .models import StaffMember


class StaffMemberSerializer(serializers.ModelSerializer):
    """Serializer for StaffMember model."""
    
    duty_status_display = serializers.CharField(source='get_duty_status_display', read_only=True)
    
    class Meta:
        model = StaffMember
        fields = [
            'staff_id',
            'name',
            'phone',
            'duty_status',
            'duty_status_display',
            'current_latitude',
            'current_longitude',
            'last_location_update',
            'is_active',
        ]
        read_only_fields = ['staff_id']
