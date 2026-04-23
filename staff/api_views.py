from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import StaffMember
from .serializers import StaffMemberSerializer
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class IsAuthority(IsAuthenticated):
    """Permission class to check if user is an authority."""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_authority


class IsStaffMember(IsAuthenticated):
    """Permission class to check if user is a staff member."""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_staff_member


class StaffListAPIView(generics.ListAPIView):
    """API endpoint for listing active staff members."""
    serializer_class = StaffMemberSerializer
    permission_classes = [IsAuthority]

    def get_queryset(self):
        return StaffMember.objects.filter(is_active=True).order_by('name')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        staff_data = []
        for staff in queryset:
            staff_dict = StaffMemberSerializer(staff).data
            staff_dict['active_complaints_count'] = staff.get_active_complaints_count()
            staff_dict['can_accept_assignment'] = staff.can_accept_assignment(max_workload=10)
            staff_data.append(staff_dict)
        return Response({'count': queryset.count(), 'results': staff_data})


class UpdateLocationAPIView(APIView):
    """
    REST endpoint for staff to update their location.
    POST /api/staff/update-location/
    Body: { latitude, longitude, accuracy (optional) }
    """
    permission_classes = [IsStaffMember]

    def post(self, request):
        try:
            staff = request.user.staff_profile
        except Exception:
            return Response({'error': 'Staff profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        accuracy = request.data.get('accuracy')

        if lat is None or lon is None:
            return Response({'error': 'latitude and longitude are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid coordinate format.'}, status=status.HTTP_400_BAD_REQUEST)

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return Response({'error': 'Coordinates out of valid range.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.utils import timezone
        from .models import LocationUpdate
        from complaints.models import Complaint

        staff.current_latitude = Decimal(str(lat))
        staff.current_longitude = Decimal(str(lon))
        staff.last_location_update = timezone.now()
        staff.save(update_fields=['current_latitude', 'current_longitude', 'last_location_update'])

        LocationUpdate.objects.create(
            staff_member=staff,
            latitude=Decimal(str(lat)),
            longitude=Decimal(str(lon)),
            accuracy=float(accuracy) if accuracy is not None else None
        )

        # Auto-update assigned complaints to in-progress
        Complaint.objects.filter(assigned_staff=staff, status='assigned').update(status='in-progress')

        return Response({
            'status': 'success',
            'message': 'Location updated.',
            'latitude': lat,
            'longitude': lon,
            'timestamp': staff.last_location_update.isoformat()
        })


class StaffDutyToggleAPIView(APIView):
    """Toggle duty status for the logged-in staff member."""
    permission_classes = [IsStaffMember]

    def post(self, request):
        try:
            staff = request.user.staff_profile
        except Exception:
            return Response({'error': 'Staff profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if staff.duty_status == 'on_duty':
            staff.duty_status = 'off_duty'
        else:
            staff.duty_status = 'on_duty'
        staff.save(update_fields=['duty_status'])

        return Response({
            'duty_status': staff.duty_status,
            'duty_status_display': staff.get_duty_status_display()
        })


class ActiveStaffLocationsAPIView(generics.ListAPIView):
    """API endpoint for getting all on-duty staff with current locations."""
    permission_classes = [IsAuthority]

    def get(self, request, *args, **kwargs):
        from django.utils import timezone
        from datetime import timedelta

        on_duty_staff = StaffMember.objects.filter(
            duty_status__in=['on_duty', 'on_break'], is_active=True
        ).select_related('user')

        staff_locations = []
        for staff in on_duty_staff:
            if staff.current_latitude and staff.current_longitude:
                if staff.last_location_update:
                    if timezone.now() - staff.last_location_update > timedelta(minutes=5):
                        continue
                staff_locations.append({
                    'staff_id': staff.staff_id,
                    'name': staff.name,
                    'latitude': float(staff.current_latitude),
                    'longitude': float(staff.current_longitude),
                    'status': staff.duty_status,
                    'assigned_complaints': staff.get_active_complaints_count(),
                    'last_update': staff.last_location_update.isoformat() if staff.last_location_update else None
                })

        return Response({'count': len(staff_locations), 'staff_locations': staff_locations})
