from rest_framework import serializers
from .models import Complaint, ComplaintPhoto
from authentication.models import User


class CitizenSerializer(serializers.ModelSerializer):
    """Serializer for citizen information in complaints."""
    
    class Meta:
        model = User
        fields = ['email', 'phone_number']


class ComplaintPhotoSerializer(serializers.ModelSerializer):
    """Serializer for complaint photos."""
    
    class Meta:
        model = ComplaintPhoto
        fields = ['id', 'photo', 'photo_type', 'uploaded_at']


class ComplaintListSerializer(serializers.ModelSerializer):
    """Serializer for complaint list view."""
    
    citizen_email = serializers.EmailField(source='citizen.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    photo_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Complaint
        fields = [
            'complaint_id',
            'citizen_email',
            'description',
            'latitude',
            'longitude',
            'address',
            'status',
            'status_display',
            'created_at',
            'assigned_staff',
            'photo_count',
        ]
    
    def get_photo_count(self, obj):
        """Get count of photos attached to complaint."""
        return obj.photos.count()


class ComplaintDetailSerializer(serializers.ModelSerializer):
    """Serializer for complaint detail view."""
    
    citizen = CitizenSerializer(read_only=True)
    photos = ComplaintPhotoSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_staff_name = serializers.CharField(source='assigned_staff.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Complaint
        fields = [
            'complaint_id',
            'citizen',
            'description',
            'latitude',
            'longitude',
            'address',
            'status',
            'status_display',
            'created_at',
            'assigned_staff',
            'assigned_staff_name',
            'assigned_at',
            'resolved_at',
            'response_time',
            'photos',
        ]
