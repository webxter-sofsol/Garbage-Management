from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PickupRequest
from .serializers import PickupRequestSerializer, CreatePickupRequestSerializer
import logging

logger = logging.getLogger(__name__)


class CreatePickupRequestAPIView(generics.CreateAPIView):
    """
    API endpoint for creating pickup requests.
    
    POST /api/pickups/create
    
    Request body:
    {
        "waste_type": "general|recyclable|organic",
        "preferred_date": "YYYY-MM-DD",
        "preferred_time": "HH:MM:SS" (optional),
        "latitude": float,
        "longitude": float,
        "address": "string",
        "notes": "string" (optional)
    }
    
    Response:
    {
        "request_id": "PKP-YYYY-XXXXXX",
        "message": "Pickup request created successfully",
        "pickup_request": {...}
    }
    """
    
    serializer_class = CreatePickupRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Create a new pickup request."""
        # Validate data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create pickup request
        pickup_request = serializer.save(citizen=request.user)
        
        logger.info(f"Pickup request {pickup_request.request_id} created by {request.user.email}")
        
        # Return response with full pickup request data
        response_serializer = PickupRequestSerializer(pickup_request)
        
        return Response({
            'request_id': pickup_request.request_id,
            'message': 'Pickup request created successfully',
            'pickup_request': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class MyPickupRequestsAPIView(generics.ListAPIView):
    """
    API endpoint for listing user's pickup requests.
    
    GET /api/pickups/my
    """
    
    serializer_class = PickupRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get pickup requests for the current user."""
        return PickupRequest.objects.filter(citizen=self.request.user).order_by('-created_at')


class PickupRequestDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving pickup request details.
    
    GET /api/pickups/{request_id}
    """
    
    serializer_class = PickupRequestSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'request_id'
    
    def get_queryset(self):
        """Get queryset with permission check."""
        user = self.request.user
        if user.is_authority or user.is_staff_member:
            # Authorities and staff can see all pickup requests
            return PickupRequest.objects.all()
        else:
            # Citizens can only see their own pickup requests
            return PickupRequest.objects.filter(citizen=user)
