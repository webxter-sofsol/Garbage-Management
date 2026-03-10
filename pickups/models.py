from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinLengthValidator
import uuid


class PickupRequest(models.Model):
    """
    Model for citizen-requested waste pickups.
    """
    WASTE_TYPE_CHOICES = [
        ('general', 'General Waste'),
        ('recyclable', 'Recyclable'),
        ('organic', 'Organic Waste'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    request_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        editable=False,
        help_text='Unique pickup request identifier (auto-generated)'
    )
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pickup_requests',
        help_text='Citizen who requested the pickup'
    )
    waste_type = models.CharField(
        max_length=20,
        choices=WASTE_TYPE_CHOICES,
        help_text='Type of waste to be collected'
    )
    preferred_date = models.DateField(
        help_text='Preferred pickup date (must be at least 24 hours in future)'
    )
    preferred_time = models.TimeField(
        null=True,
        blank=True,
        help_text='Preferred pickup time (optional)'
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text='Latitude coordinate (-90 to 90)'
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text='Longitude coordinate (-180 to 180)'
    )
    address = models.TextField(
        help_text='Pickup address'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        validators=[MinLengthValidator(10)],
        help_text='Additional notes or instructions (optional, min 10 characters)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text='Current status of the pickup request'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Timestamp when request was created'
    )
    scheduled_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual scheduled pickup date'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when pickup was completed'
    )
    assigned_staff = models.ForeignKey(
        'staff.StaffMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_pickups',
        help_text='Staff member assigned to this pickup'
    )
    
    class Meta:
        db_table = 'pickup_requests'
        verbose_name = 'Pickup Request'
        verbose_name_plural = 'Pickup Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_id']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['citizen', 'status']),
            models.Index(fields=['preferred_date']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.request_id} - {self.get_waste_type_display()} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Generate request ID if not set."""
        if not self.request_id:
            self.request_id = self.generate_request_id()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_request_id():
        """Generate unique request ID in format PKP-YYYY-XXXXXX."""
        year = timezone.now().year
        unique_id = str(uuid.uuid4().int)[:6]
        return f"PKP-{year}-{unique_id}"
    
    def mark_scheduled(self, scheduled_date):
        """Mark pickup as scheduled."""
        self.status = 'scheduled'
        self.scheduled_date = scheduled_date
        self.save(update_fields=['status', 'scheduled_date'])
    
    def mark_completed(self):
        """Mark pickup as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_cancelled(self):
        """Mark pickup as cancelled."""
        self.status = 'cancelled'
        self.save(update_fields=['status'])
