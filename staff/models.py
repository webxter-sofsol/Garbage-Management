from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid


class StaffMember(models.Model):
    """
    Model for collection staff members.
    """
    DUTY_STATUS_CHOICES = [
        ('on_duty', 'On Duty'),
        ('off_duty', 'Off Duty'),
        ('on_break', 'On Break'),
    ]
    
    staff_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        editable=False,
        help_text='Unique staff identifier (auto-generated)'
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        help_text='User account linked to this staff member'
    )
    name = models.CharField(
        max_length=100,
        help_text='Full name of the staff member'
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        help_text='Contact phone number'
    )
    duty_status = models.CharField(
        max_length=20,
        choices=DUTY_STATUS_CHOICES,
        default='off_duty',
        db_index=True,
        help_text='Current duty status'
    )
    current_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='Current latitude coordinate'
    )
    current_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='Current longitude coordinate'
    )
    last_location_update = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp of last location update'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='Timestamp when staff member was added'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this staff member is active'
    )
    
    class Meta:
        db_table = 'staff_members'
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'
        ordering = ['name']
        indexes = [
            models.Index(fields=['staff_id']),
            models.Index(fields=['duty_status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['current_latitude', 'current_longitude']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.staff_id})"
    
    def save(self, *args, **kwargs):
        """Generate staff ID if not set."""
        if not self.staff_id:
            self.staff_id = self.generate_staff_id()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_staff_id():
        """Generate unique staff ID in format STF-XXXXXX."""
        unique_id = str(uuid.uuid4().int)[:6]
        return f"STF-{unique_id}"
    
    def update_location(self, latitude, longitude):
        """Update staff member's current location."""
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_latitude', 'current_longitude', 'last_location_update'])
        
        # Create location history record
        LocationUpdate.objects.create(
            staff_member=self,
            latitude=latitude,
            longitude=longitude
        )
    
    def set_duty_status(self, status):
        """Update duty status."""
        if status in dict(self.DUTY_STATUS_CHOICES):
            self.duty_status = status
            self.save(update_fields=['duty_status'])
    
    def get_active_complaints_count(self):
        """Get count of active complaints assigned to this staff member."""
        return self.assigned_complaints.filter(
            status__in=['assigned', 'in-progress']
        ).count()
    
    def can_accept_assignment(self, max_workload=10):
        """Check if staff member can accept new assignments."""
        return self.get_active_complaints_count() < max_workload


class LocationUpdate(models.Model):
    """
    Model for tracking staff location history.
    """
    staff_member = models.ForeignKey(
        StaffMember,
        on_delete=models.CASCADE,
        related_name='location_updates',
        help_text='Staff member this location update belongs to'
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text='Latitude coordinate'
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text='Longitude coordinate'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Timestamp of this location update'
    )
    accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text='GPS accuracy in meters (optional)'
    )
    
    class Meta:
        db_table = 'location_updates'
        verbose_name = 'Location Update'
        verbose_name_plural = 'Location Updates'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['staff_member', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.staff_member.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
