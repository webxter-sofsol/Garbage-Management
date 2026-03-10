"""
WebSocket consumers for real-time location tracking.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class LocationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for receiving and broadcasting staff location updates.
    """
    
    async def connect(self):
        """Accept WebSocket connection."""
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        pass
    
    async def receive(self, text_data):
        """
        Receive location update from staff member.
        Expected format:
        {
            "staff_id": "STF-001",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "timestamp": "2024-01-15T10:30:00Z",
            "accuracy": 10.5
        }
        """
        try:
            data = json.loads(text_data)
            
            # Validate required fields
            staff_id = data.get('staff_id')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if not all([staff_id, latitude is not None, longitude is not None]):
                await self.send(text_data=json.dumps({
                    'error': 'Missing required fields: staff_id, latitude, longitude'
                }))
                return
            
            # Validate coordinate ranges
            try:
                lat = float(latitude)
                lon = float(longitude)
                
                if not (-90 <= lat <= 90):
                    await self.send(text_data=json.dumps({
                        'error': 'Invalid latitude: must be between -90 and 90'
                    }))
                    return
                
                if not (-180 <= lon <= 180):
                    await self.send(text_data=json.dumps({
                        'error': 'Invalid longitude: must be between -180 and 180'
                    }))
                    return
            except (ValueError, TypeError):
                await self.send(text_data=json.dumps({
                    'error': 'Invalid coordinate format'
                }))
                return
            
            # Get optional accuracy
            accuracy = data.get('accuracy')
            if accuracy is not None:
                try:
                    accuracy = float(accuracy)
                except (ValueError, TypeError):
                    accuracy = None
            
            # Update staff location in database
            result = await self.update_staff_location(
                staff_id, lat, lon, accuracy
            )
            
            if result['success']:
                # Send success response
                await self.send(text_data=json.dumps({
                    'status': 'success',
                    'message': 'Location updated successfully',
                    'staff_id': staff_id,
                    'timestamp': timezone.now().isoformat()
                }))
            else:
                # Send error response
                await self.send(text_data=json.dumps({
                    'error': result.get('error', 'Failed to update location')
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Server error: {str(e)}'
            }))
    
    @database_sync_to_async
    def update_staff_location(self, staff_id, latitude, longitude, accuracy=None):
        """
        Update staff member location in database.
        Returns dict with success status and optional error message.
        """
        from .models import StaffMember, LocationUpdate
        
        try:
            # Find staff member
            staff = StaffMember.objects.get(staff_id=staff_id)
            
            # Check if staff is on duty
            if staff.duty_status == 'off_duty':
                return {
                    'success': False,
                    'error': 'Staff member is not on duty'
                }
            
            # Check if update is too frequent (less than 30 seconds since last update)
            if staff.last_location_update:
                time_since_last = timezone.now() - staff.last_location_update
                if time_since_last < timedelta(seconds=30):
                    return {
                        'success': False,
                        'error': f'Location updates must be at least 30 seconds apart. Wait {30 - time_since_last.seconds} seconds.'
                    }
            
            # Update staff member's current location
            staff.current_latitude = Decimal(str(latitude))
            staff.current_longitude = Decimal(str(longitude))
            staff.last_location_update = timezone.now()
            staff.save(update_fields=['current_latitude', 'current_longitude', 'last_location_update'])
            
            # Create location history record
            LocationUpdate.objects.create(
                staff_member=staff,
                latitude=Decimal(str(latitude)),
                longitude=Decimal(str(longitude)),
                accuracy=accuracy
            )
            
            # Update assigned complaints to "in-progress" if staff is traveling
            self._update_complaint_status(staff)
            
            return {'success': True}
        
        except StaffMember.DoesNotExist:
            return {
                'success': False,
                'error': f'Staff member with ID {staff_id} not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
    
    def _update_complaint_status(self, staff):
        """
        Update complaint status to 'in-progress' for assigned complaints
        when staff is traveling (has location updates).
        """
        from complaints.models import Complaint
        
        # Get assigned complaints that are not yet in-progress or resolved
        assigned_complaints = Complaint.objects.filter(
            assigned_staff=staff,
            status='assigned'
        )
        
        # Update status to in-progress
        for complaint in assigned_complaints:
            complaint.status = 'in-progress'
            complaint.save(update_fields=['status'])
