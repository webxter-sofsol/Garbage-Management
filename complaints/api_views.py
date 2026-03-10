from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import Complaint, ComplaintPhoto
from .serializers import ComplaintListSerializer, ComplaintDetailSerializer
from .validators import ComplaintValidator
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


class ComplaintListAPIView(generics.ListAPIView):
    """
    API endpoint for listing complaints with filtering and sorting.
    
    Query Parameters:
    - status: Filter by status (pending, assigned, in-progress, resolved, closed)
    - date_from: Filter complaints created after this date (YYYY-MM-DD)
    - date_to: Filter complaints created before this date (YYYY-MM-DD)
    - lat_min, lat_max: Filter by latitude range
    - lon_min, lon_max: Filter by longitude range
    - search: Search in description and address
    - ordering: Sort by field (created_at, status, latitude, longitude)
                Prefix with '-' for descending order
    """
    
    serializer_class = ComplaintListSerializer
    permission_classes = [IsAuthority]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at', 'status', 'latitude', 'longitude']
    ordering = ['-created_at']  # Default ordering
    search_fields = ['description', 'address', 'complaint_id']
    
    def get_queryset(self):
        """Get filtered queryset based on query parameters."""
        queryset = Complaint.objects.select_related('citizen', 'assigned_staff').prefetch_related('photos')
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=date_from_obj)
            except ValueError:
                logger.warning(f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                queryset = queryset.filter(created_at__lte=date_to_obj)
            except ValueError:
                logger.warning(f"Invalid date_to format: {date_to}")
        
        # Filter by location (bounding box)
        lat_min = self.request.query_params.get('lat_min', None)
        lat_max = self.request.query_params.get('lat_max', None)
        lon_min = self.request.query_params.get('lon_min', None)
        lon_max = self.request.query_params.get('lon_max', None)
        
        if lat_min:
            try:
                queryset = queryset.filter(latitude__gte=float(lat_min))
            except ValueError:
                logger.warning(f"Invalid lat_min: {lat_min}")
        
        if lat_max:
            try:
                queryset = queryset.filter(latitude__lte=float(lat_max))
            except ValueError:
                logger.warning(f"Invalid lat_max: {lat_max}")
        
        if lon_min:
            try:
                queryset = queryset.filter(longitude__gte=float(lon_min))
            except ValueError:
                logger.warning(f"Invalid lon_min: {lon_min}")
        
        if lon_max:
            try:
                queryset = queryset.filter(longitude__lte=float(lon_max))
            except ValueError:
                logger.warning(f"Invalid lon_max: {lon_max}")
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Override list to add metadata to response."""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Add metadata
        response_data = {
            'count': queryset.count(),
            'results': serializer.data,
            'filters_applied': {
                'status': request.query_params.get('status'),
                'date_from': request.query_params.get('date_from'),
                'date_to': request.query_params.get('date_to'),
                'location_filter': bool(
                    request.query_params.get('lat_min') or 
                    request.query_params.get('lat_max') or
                    request.query_params.get('lon_min') or
                    request.query_params.get('lon_max')
                ),
            }
        }
        
        return Response(response_data)


class ComplaintDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving complaint details.
    
    Returns complete complaint information including citizen contact details.
    """
    
    serializer_class = ComplaintDetailSerializer
    permission_classes = [IsAuthority]
    lookup_field = 'complaint_id'
    
    def get_queryset(self):
        """Get queryset with related data."""
        return Complaint.objects.select_related(
            'citizen', 
            'assigned_staff'
        ).prefetch_related('photos')
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to log access."""
        instance = self.get_object()
        logger.info(f"Complaint {instance.complaint_id} accessed by {request.user.email}")
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AssignStaffAPIView(generics.UpdateAPIView):
    """
    API endpoint for assigning staff to complaints.
    
    PUT /api/complaints/{complaint_id}/assign
    
    Request Body:
    {
        "staff_id": "STF-123456"
    }
    
    Validates:
    - Staff member exists and is active
    - Staff member workload is below limit (max 10 active complaints)
    - Complaint is in assignable status (pending or assigned)
    
    Updates:
    - Complaint status to "assigned"
    - Assigned staff member
    - Assignment timestamp
    """
    
    permission_classes = [IsAuthority]
    lookup_field = 'complaint_id'
    
    def get_queryset(self):
        """Get queryset."""
        return Complaint.objects.all()
    
    def update(self, request, *args, **kwargs):
        """Assign staff to complaint with workload validation."""
        from staff.models import StaffMember
        
        complaint = self.get_object()
        staff_id = request.data.get('staff_id')
        
        # Validate staff_id provided
        if not staff_id:
            return Response(
                {'error': 'staff_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get staff member
        try:
            staff_member = StaffMember.objects.get(staff_id=staff_id, is_active=True)
        except StaffMember.DoesNotExist:
            return Response(
                {'error': f'Staff member {staff_id} not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check workload limit
        if not staff_member.can_accept_assignment(max_workload=10):
            active_count = staff_member.get_active_complaints_count()
            return Response(
                {
                    'error': f'Staff member {staff_id} has reached maximum workload',
                    'active_complaints': active_count,
                    'max_workload': 10
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check complaint status
        if complaint.status not in ['pending', 'assigned']:
            return Response(
                {
                    'error': f'Cannot assign staff to complaint with status "{complaint.status}"',
                    'allowed_statuses': ['pending', 'assigned']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Assign staff to complaint
        complaint.assign_to_staff(staff_member)
        
        logger.info(
            f"Complaint {complaint.complaint_id} assigned to staff {staff_id} "
            f"by authority {request.user.email}"
        )
        
        # Return updated complaint details
        serializer = ComplaintDetailSerializer(complaint)
        return Response({
            'message': f'Complaint {complaint.complaint_id} successfully assigned to {staff_member.name}',
            'complaint': serializer.data
        }, status=status.HTTP_200_OK)


class ResolveComplaintAPIView(generics.UpdateAPIView):
    """
    API endpoint for resolving complaints.
    
    PUT /api/complaints/{complaint_id}/resolve
    
    Request Body (multipart/form-data):
    {
        "after_photos": [File, File, ...]  # At least one required
    }
    
    Validates:
    - At least one "after" photo is provided
    - Complaint is in resolvable status (assigned or in-progress)
    - User is the assigned staff member or an authority
    
    Updates:
    - Complaint status to "resolved"
    - Resolution timestamp
    - Response time calculation
    - Stores after photos
    """
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'complaint_id'
    
    def get_queryset(self):
        """Get queryset."""
        return Complaint.objects.all()
    
    def update(self, request, *args, **kwargs):
        """Resolve complaint with after photos."""
        complaint = self.get_object()
        after_photos = request.FILES.getlist('after_photos')
        
        # Validate user permission
        if not (request.user.is_authority or 
                (request.user.is_staff_member and 
                 hasattr(request.user, 'staff_profile') and
                 complaint.assigned_staff == request.user.staff_profile)):
            return Response(
                {'error': 'You do not have permission to resolve this complaint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate at least one after photo is provided
        if not after_photos or len(after_photos) == 0:
            return Response(
                {
                    'error': 'At least one "after" photo is required to resolve a complaint',
                    'field': 'after_photos'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate complaint status
        if complaint.status not in ['assigned', 'in-progress']:
            return Response(
                {
                    'error': f'Cannot resolve complaint with status "{complaint.status}"',
                    'allowed_statuses': ['assigned', 'in-progress']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate photo files
        for photo in after_photos:
            is_valid, error = ComplaintValidator.validate_photo(photo)
            if not is_valid:
                return Response(
                    {
                        'error': f'Invalid photo file: {error}',
                        'file_name': photo.name
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            # Save after photos
            for photo in after_photos:
                ComplaintPhoto.objects.create(
                    complaint=complaint,
                    photo=photo,
                    photo_type='after'
                )
            
            # Mark complaint as resolved
            complaint.status = 'resolved'
            complaint.resolved_at = timezone.now()
            
            # Calculate response time
            if complaint.created_at:
                complaint.response_time = complaint.resolved_at - complaint.created_at
            
            complaint.save(update_fields=['status', 'resolved_at', 'response_time'])
            
            logger.info(
                f"Complaint {complaint.complaint_id} resolved by {request.user.email} "
                f"with {len(after_photos)} after photo(s)"
            )
            
            # Return updated complaint details
            serializer = ComplaintDetailSerializer(complaint)
            return Response({
                'message': f'Complaint {complaint.complaint_id} successfully resolved',
                'complaint': serializer.data,
                'after_photos_count': len(after_photos)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error resolving complaint {complaint.complaint_id}: {str(e)}")
            return Response(
                {
                    'error': 'An error occurred while resolving the complaint',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
