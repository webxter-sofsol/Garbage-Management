from django.db import models
import math


class BinLocation(models.Model):
    BIN_TYPE_CHOICES = [
        ('general', 'General Waste'),
        ('recyclable', 'Recyclable'),
        ('organic', 'Organic'),
    ]

    bin_id = models.CharField(max_length=50, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.TextField()
    bin_type = models.CharField(max_length=20, choices=BIN_TYPE_CHOICES)
    collection_schedule = models.TextField(help_text="e.g. Mon, Wed, Fri - 8AM to 12PM")
    capacity = models.CharField(max_length=50, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bin_locations'
        indexes = [
            models.Index(fields=['bin_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.bin_id} - {self.get_bin_type_display()} at {self.address[:40]}"

    def distance_to(self, lat, lon):
        """Calculate distance in km using Haversine formula."""
        R = 6371
        lat1, lon1 = math.radians(float(self.latitude)), math.radians(float(self.longitude))
        lat2, lon2 = math.radians(float(lat)), math.radians(float(lon))
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))
