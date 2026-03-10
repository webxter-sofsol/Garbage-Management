from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import StaffMember
from .serializers import StaffMemberSerializer
import logging

logger = logging.getLogger(__name__)


class IsAuthority(IsAuthenticated):
    """Permission class to check if user is an authority."""
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_authority


class StaffListAPIView(generics.ListAPIView):
    """
    API endpoint for listing active staff members.
    
    Returns all active staff members with their current workload.
    """
    
    serializer_class = StaffMemberSerializer
    permission_classes = [IsAuthority]
    
    def get_queryset(self):
        """Get all active staff members."""
        return StaffMember.objects.filter(is_active=True).order_by('name')
    
    def list(self, request, *args, **kwargs):
        """Override list to add workload information."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Add workload info to each staff member
        staff_data = []
        for staff in queryset:
            staff_dict = StaffMemberSerializer(staff).data
            staff_dict['active_complaints_count'] = staff.get_active_complaints_count()
            staff_dict['can_accept_assignment'] = staff.can_accept_assignment(max_workload=10)
            staff_data.append(staff_dict)
        
        return Response({
            'count': queryset.count(),
            'results': staff_data
        })


class ActiveStaffLocationsAPIView(generics.ListAPIView):
    """
    API endpoint for getting all on-duty staff with current locations.
    
    Returns staff members who are on duty with their current locations,
    status, and assigned complaint count.
    """
    
    permission_classes = [IsAuthority]
    
    def get(self, request, *args, **kwargs):
        """Get all on-duty staff with location data."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Get staff members who are on duty
        on_duty_staff = StaffMember.objects.filter(
            duty_status__in=['on_duty', 'on_break'],
            is_active=True
        ).select_related('user')
        
        staff_locations = []
        
        for staff in on_duty_staff:
            # Only include staff with recent location updates (within last 5 minutes)
            if staff.current_latitude and staff.current_longitude:
                if staff.last_location_update:
                    time_since_update = timezone.now() - staff.last_location_update
                    if time_since_update > timedelta(minutes=5):
                        # Location is stale, skip this staff member
                        continue
                
                # Get assigned complaints count
                assigned_count = staff.get_active_complaints_count()
                
                staff_data = {
                    'staff_id': staff.staff_id,
                    'name': staff.name,
                    'latitude': float(staff.current_latitude),
                    'longitude': float(staff.current_longitude),
                    'status': staff.duty_status,
                    'assigned_complaints': assigned_count,
                    'last_update': staff.last_location_update.isoformat() if staff.last_location_update else None
                }
                
                staff_locations.append(staff_data)
        
        return Response({
            'count': len(staff_locations),
            'staff_locations': staff_locations
        })
