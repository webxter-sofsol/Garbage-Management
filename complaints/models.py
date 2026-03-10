from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator
import uuid


class Complaint(models.Model):
    """
    Model for citizen-reported waste management complaints.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in-progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    complaint_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        editable=False,
        help_text='Unique complaint identifier (auto-generated)'
    )
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints',
        help_text='Citizen who filed the complaint'
    )
    description = models.TextField(
        validators=[MinLengthValidator(10), MaxLengthValidator(500)],
        help_text='Complaint description (10-500 characters)'
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
        blank=True,
        null=True,
        help_text='Human-readable address from reverse geocoding'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text='Current status of the complaint'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Timestamp when complaint was created'
    )
    assigned_staff = models.ForeignKey(
        'staff.StaffMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        help_text='Staff member assigned to this complaint'
    )
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when staff was assigned'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when complaint was resolved'
    )
    response_time = models.DurationField(
        null=True,
        blank=True,
        help_text='Time taken from creation to resolution'
    )
    
    class Meta:
        db_table = 'complaints'
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['complaint_id']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['citizen', 'status']),
            models.Index(fields=['assigned_staff', 'status']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.complaint_id} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Generate complaint ID if not set."""
        if not self.complaint_id:
            self.complaint_id = self.generate_complaint_id()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_complaint_id():
        """Generate unique complaint ID in format CMP-YYYY-XXXXXX."""
        year = timezone.now().year
        unique_id = str(uuid.uuid4().int)[:6]
        return f"CMP-{year}-{unique_id}"
    
    def calculate_response_time(self):
        """Calculate response time from creation to resolution."""
        if self.resolved_at and self.created_at:
            self.response_time = self.resolved_at - self.created_at
            self.save(update_fields=['response_time'])
    
    def assign_to_staff(self, staff_member):
        """Assign complaint to a staff member."""
        self.assigned_staff = staff_member
        self.assigned_at = timezone.now()
        self.status = 'assigned'
        self.save(update_fields=['assigned_staff', 'assigned_at', 'status'])
    
    def mark_in_progress(self):
        """Mark complaint as in progress."""
        self.status = 'in-progress'
        self.save(update_fields=['status'])
    
    def mark_resolved(self):
        """Mark complaint as resolved and calculate response time."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.calculate_response_time()
        self.save(update_fields=['status', 'resolved_at'])
    
    def mark_closed(self):
        """Mark complaint as closed."""
        self.status = 'closed'
        self.save(update_fields=['status'])


class ComplaintPhoto(models.Model):
    """
    Model for photos attached to complaints.
    """
    PHOTO_TYPE_CHOICES = [
        ('before', 'Before'),
        ('after', 'After'),
    ]
    
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='photos',
        help_text='Complaint this photo belongs to'
    )
    photo = models.ImageField(
        upload_to='complaints/%Y/%m/%d/',
        help_text='Photo file (max 5MB)'
    )
    photo_type = models.CharField(
        max_length=10,
        choices=PHOTO_TYPE_CHOICES,
        default='before',
        db_index=True,
        help_text='Type of photo (before/after)'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when photo was uploaded'
    )
    
    class Meta:
        db_table = 'complaint_photos'
        verbose_name = 'Complaint Photo'
        verbose_name_plural = 'Complaint Photos'
        ordering = ['uploaded_at']
        indexes = [
            models.Index(fields=['complaint', 'photo_type']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.complaint.complaint_id} - {self.get_photo_type_display()} photo"
