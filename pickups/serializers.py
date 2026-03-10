from rest_framework import serializers
from .models import PickupRequest
from authentication.models import User


class PickupRequestSerializer(serializers.ModelSerializer):
    """Serializer for pickup requests."""
    
    citizen_email = serializers.EmailField(source='citizen.email', read_only=True)
    waste_type_display = serializers.CharField(source='get_waste_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PickupRequest
        fields = [
            'request_id',
            'citizen_email',
            'waste_type',
            'waste_type_display',
            'preferred_date',
            'preferred_time',
            'latitude',
            'longitude',
            'address',
            'notes',
            'status',
            'status_display',
            'created_at',
            'scheduled_date',
            'completed_at',
        ]
        read_only_fields = ['request_id', 'created_at', 'scheduled_date', 'completed_at']


class CreatePickupRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating pickup requests."""
    
    class Meta:
        model = PickupRequest
        fields = [
            'waste_type',
            'preferred_date',
            'preferred_time',
            'latitude',
            'longitude',
            'address',
            'notes',
        ]
    
    def validate(self, data):
        """Validate pickup request data."""
        from .validators import PickupRequestValidator
        
        is_valid, errors = PickupRequestValidator.validate_pickup_request_data(
            waste_type=data.get('waste_type'),
            preferred_date=data.get('preferred_date'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            address=data.get('address'),
            notes=data.get('notes')
        )
        
        if not is_valid:
            raise serializers.ValidationError(errors)
        
        return data
