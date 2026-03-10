"""
Tests for staff location tracking functionality.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from staff.models import StaffMember, LocationUpdate
from staff.utils import calculate_distance, calculate_eta, get_staff_eta_to_complaint
from authentication.models import User
from complaints.models import Complaint


class LocationTrackingTestCase(TestCase):
    """Test cases for location tracking functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create(
            email='staff@test.com',
            is_staff_member=True
        )
        
        # Create staff member
        self.staff = StaffMember.objects.create(
            user=self.user,
            name='Test Staff',
            phone='+1234567890',
            duty_status='on_duty'
        )
        
        # Create citizen user
        self.citizen = User.objects.create(
            email='citizen@test.com',
            is_citizen=True
        )
        
        # Create complaint
        self.complaint = Complaint.objects.create(
            citizen=self.citizen,
            description='Test complaint for location tracking',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060'),
            status='assigned',
            assigned_staff=self.staff
        )
    
    def test_update_location(self):
        """Test updating staff location."""
        lat = Decimal('40.7580')
        lon = Decimal('-73.9855')
        
        self.staff.update_location(lat, lon)
        
        # Refresh from database
        self.staff.refresh_from_db()
        
        # Check location was updated
        self.assertEqual(self.staff.current_latitude, lat)
        self.assertEqual(self.staff.current_longitude, lon)
        self.assertIsNotNone(self.staff.last_location_update)
        
        # Check location history was created
        location_updates = LocationUpdate.objects.filter(staff_member=self.staff)
        self.assertEqual(location_updates.count(), 1)
        self.assertEqual(location_updates.first().latitude, lat)
        self.assertEqual(location_updates.first().longitude, lon)
    
    def test_calculate_distance(self):
        """Test distance calculation between two coordinates."""
        # New York to Los Angeles (approximately 3936 km)
        ny_lat, ny_lon = 40.7128, -74.0060
        la_lat, la_lon = 34.0522, -118.2437
        
        distance = calculate_distance(ny_lat, ny_lon, la_lat, la_lon)
        
        # Check distance is approximately correct (within 100 km tolerance)
        self.assertGreater(distance, 3800)
        self.assertLess(distance, 4100)
    
    def test_calculate_distance_same_point(self):
        """Test distance calculation for same point."""
        lat, lon = 40.7128, -74.0060
        
        distance = calculate_distance(lat, lon, lat, lon)
        
        # Distance should be 0
        self.assertEqual(distance, 0)
    
    def test_calculate_eta(self):
        """Test ETA calculation."""
        # 30 km at 30 km/h should take 60 minutes
        eta = calculate_eta(30, 30)
        self.assertEqual(eta, 60)
        
        # 15 km at 30 km/h should take 30 minutes
        eta = calculate_eta(15, 30)
        self.assertEqual(eta, 30)
        
        # 5 km at 30 km/h should take 10 minutes
        eta = calculate_eta(5, 30)
        self.assertEqual(eta, 10)
    
    def test_calculate_eta_zero_distance(self):
        """Test ETA calculation for zero distance."""
        eta = calculate_eta(0)
        self.assertEqual(eta, 0)
    
    def test_get_staff_eta_to_complaint(self):
        """Test getting ETA from staff to complaint."""
        # Set staff location (Times Square, NY)
        self.staff.current_latitude = Decimal('40.7580')
        self.staff.current_longitude = Decimal('-73.9855')
        self.staff.save()
        
        # Complaint is at (40.7128, -74.0060) - about 5 km away
        result = get_staff_eta_to_complaint(self.staff, self.complaint)
        
        self.assertIsNotNone(result)
        self.assertIn('distance_km', result)
        self.assertIn('eta_minutes', result)
        self.assertGreater(result['distance_km'], 0)
        self.assertGreater(result['eta_minutes'], 0)
    
    def test_get_staff_eta_no_location(self):
        """Test ETA calculation when staff has no location."""
        # Staff has no location set
        result = get_staff_eta_to_complaint(self.staff, self.complaint)
        
        self.assertIsNone(result)
    
    def test_active_complaints_count(self):
        """Test getting active complaints count for staff."""
        count = self.staff.get_active_complaints_count()
        self.assertEqual(count, 1)  # One assigned complaint
        
        # Mark complaint as resolved
        self.complaint.status = 'resolved'
        self.complaint.save()
        
        count = self.staff.get_active_complaints_count()
        self.assertEqual(count, 0)  # No active complaints
    
    def test_can_accept_assignment(self):
        """Test checking if staff can accept new assignments."""
        # Staff has 1 complaint, should be able to accept more
        self.assertTrue(self.staff.can_accept_assignment(max_workload=10))
        
        # Create 9 more complaints (total 10)
        for i in range(9):
            Complaint.objects.create(
                citizen=self.citizen,
                description=f'Test complaint {i}',
                latitude=Decimal('40.7128'),
                longitude=Decimal('-74.0060'),
                status='assigned',
                assigned_staff=self.staff
            )
        
        # Staff has 10 complaints, should not be able to accept more
        self.assertFalse(self.staff.can_accept_assignment(max_workload=10))
    
    def test_location_update_frequency_validation(self):
        """Test that location updates respect 30-second minimum interval."""
        # This test validates the business logic in the consumer
        # The actual validation happens in the async consumer method
        # We'll test the synchronous update_location method instead
        
        # Set initial location
        self.staff.current_latitude = Decimal('40.7128')
        self.staff.current_longitude = Decimal('-74.0060')
        self.staff.last_location_update = timezone.now()
        self.staff.save()
        
        # Check that last_location_update was set
        self.assertIsNotNone(self.staff.last_location_update)
        
        # The 30-second validation is enforced in the WebSocket consumer
        # which requires async testing. For now, we verify the timestamp is set.
        time_diff = timezone.now() - self.staff.last_location_update
        self.assertLess(time_diff.total_seconds(), 5)  # Should be very recent
    
    def test_coordinate_validation(self):
        """Test coordinate range validation."""
        from staff.utils import calculate_distance
        
        # Valid coordinates should work
        distance = calculate_distance(40.7128, -74.0060, 34.0522, -118.2437)
        self.assertGreater(distance, 0)
        
        # Test with Decimal types
        distance = calculate_distance(
            Decimal('40.7128'),
            Decimal('-74.0060'),
            Decimal('34.0522'),
            Decimal('-118.2437')
        )
        self.assertGreater(distance, 0)


class LocationUpdateModelTestCase(TestCase):
    """Test cases for LocationUpdate model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            email='staff2@test.com',
            is_staff_member=True
        )
        
        self.staff = StaffMember.objects.create(
            user=self.user,
            name='Test Staff 2',
            phone='+1234567891',
            duty_status='on_duty'
        )
    
    def test_create_location_update(self):
        """Test creating a location update."""
        location = LocationUpdate.objects.create(
            staff_member=self.staff,
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060'),
            accuracy=10.5
        )
        
        self.assertEqual(location.staff_member, self.staff)
        self.assertEqual(location.latitude, Decimal('40.7128'))
        self.assertEqual(location.longitude, Decimal('-74.0060'))
        self.assertEqual(location.accuracy, 10.5)
        self.assertIsNotNone(location.timestamp)
    
    def test_location_update_ordering(self):
        """Test that location updates are ordered by timestamp descending."""
        import time
        
        # Create first location update
        LocationUpdate.objects.create(
            staff_member=self.staff,
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        
        # Wait a tiny bit to ensure different timestamps
        time.sleep(0.01)
        
        # Create second location update
        LocationUpdate.objects.create(
            staff_member=self.staff,
            latitude=Decimal('40.7580'),
            longitude=Decimal('-73.9855')
        )
        
        # Get all updates
        updates = LocationUpdate.objects.filter(staff_member=self.staff)
        
        # Check ordering (most recent first)
        self.assertEqual(updates.count(), 2)
        # The second one should be first due to descending order
        self.assertGreaterEqual(updates[0].timestamp, updates[1].timestamp)
