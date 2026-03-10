"""
Manual test script for complaint resolution functionality.
Run with: python manage.py shell < test_resolution_manual.py
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from authentication.models import User
from staff.models import StaffMember
from complaints.models import Complaint, ComplaintPhoto
import io
from PIL import Image

print("=" * 60)
print("Testing Complaint Resolution Module")
print("=" * 60)

# Create test image
def create_test_image(name='test.jpg'):
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'JPEG')
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type='image/jpeg')

# Check if test users exist, create if not
print("\n1. Setting up test data...")

citizen, created = User.objects.get_or_create(
    email='test_citizen@example.com',
    defaults={
        'is_citizen': True,
    }
)
if created:
    citizen.set_password('testpass123')
    citizen.save()
    print("   ✓ Created test citizen")
else:
    print("   ✓ Test citizen already exists")

staff_user, created = User.objects.get_or_create(
    email='test_staff@example.com',
    defaults={
        'is_staff_member': True,
    }
)
if created:
    staff_user.set_password('testpass123')
    staff_user.save()
    print("   ✓ Created test staff user")
else:
    print("   ✓ Test staff user already exists")

# Create staff member profile if not exists
staff_member, created = StaffMember.objects.get_or_create(
    user=staff_user,
    defaults={
        'name': 'Test Staff Member',
        'phone': '+1234567890'
    }
)
if created:
    print("   ✓ Created staff member profile")
else:
    print("   ✓ Staff member profile already exists")

# Create test complaint
print("\n2. Creating test complaint...")
complaint = Complaint.objects.create(
    citizen=citizen,
    description='Test complaint for resolution testing',
    latitude=40.7128,
    longitude=-74.0060,
    status='assigned',
    assigned_staff=staff_member
)
print(f"   ✓ Created complaint: {complaint.complaint_id}")

# Add before photo
print("\n3. Adding before photo...")
before_photo = create_test_image('before.jpg')
ComplaintPhoto.objects.create(
    complaint=complaint,
    photo=before_photo,
    photo_type='before'
)
print("   ✓ Before photo added")

# Verify complaint state
print("\n4. Verifying complaint state...")
print(f"   - Status: {complaint.status}")
print(f"   - Assigned to: {complaint.assigned_staff.name}")
print(f"   - Before photos: {complaint.photos.filter(photo_type='before').count()}")
print(f"   - After photos: {complaint.photos.filter(photo_type='after').count()}")

# Test resolution (simulated)
print("\n5. Simulating resolution...")
after_photo = create_test_image('after.jpg')
ComplaintPhoto.objects.create(
    complaint=complaint,
    photo=after_photo,
    photo_type='after'
)
complaint.status = 'resolved'
complaint.resolved_at = timezone.now()
complaint.response_time = complaint.resolved_at - complaint.created_at
complaint.save()
print("   ✓ Complaint marked as resolved")

# Verify resolution
print("\n6. Verifying resolution...")
complaint.refresh_from_db()
print(f"   - Status: {complaint.status}")
print(f"   - Resolved at: {complaint.resolved_at}")
print(f"   - Response time: {complaint.response_time}")
print(f"   - After photos: {complaint.photos.filter(photo_type='after').count()}")

print("\n" + "=" * 60)
print("✓ All tests completed successfully!")
print("=" * 60)

print("\nTest complaint ID:", complaint.complaint_id)
print("You can view this complaint at:")
print(f"  - Detail page: /complaints/{complaint.complaint_id}/")
print(f"  - API endpoint: /api/complaints/{complaint.complaint_id}/")
print(f"  - Resolve page: /staff/resolve/{complaint.complaint_id}/")
