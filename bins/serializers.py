from rest_framework import serializers
from .models import BinLocation


class BinLocationSerializer(serializers.ModelSerializer):
    bin_type_display = serializers.CharField(source='get_bin_type_display', read_only=True)
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = BinLocation
        fields = [
            'bin_id', 'latitude', 'longitude', 'address', 'bin_type',
            'bin_type_display', 'collection_schedule', 'capacity',
            'is_active', 'distance_km'
        ]

    def get_distance_km(self, obj):
        """Calculate distance if user location is provided in context."""
        user_lat = self.context.get('user_latitude')
        user_lon = self.context.get('user_longitude')
        if user_lat and user_lon:
            return round(obj.distance_to(user_lat, user_lon), 2)
        return None
