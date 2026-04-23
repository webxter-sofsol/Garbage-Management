from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import BinLocation
from .serializers import BinLocationSerializer
import logging

logger = logging.getLogger(__name__)


class BinLocationListAPIView(generics.ListAPIView):
    """
    API endpoint for listing bin locations with optional filtering.
    
    GET /api/bins/nearby
    
    Query Parameters:
    - latitude: User's latitude (optional)
    - longitude: User's longitude (optional)
    - radius_km: Search radius in km (default: 5, max: 50)
    - bin_type: Filter by bin type (general/recyclable/organic)
    
    Returns list of bins sorted by distance if location provided.
    """
    
    serializer_class = BinLocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get filtered queryset."""
        queryset = BinLocation.objects.filter(is_active=True)
        
        # Filter by bin type
        bin_type = self.request.query_params.get('bin_type')
        if bin_type:
            queryset = queryset.filter(bin_type=bin_type)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List bins with distance calculation."""
        queryset = self.get_queryset()
        
        # Get user location
        user_lat = request.query_params.get('latitude')
        user_lon = request.query_params.get('longitude')
        radius_km = float(request.query_params.get('radius_km', 5))
        
        # Validate radius
        if radius_km > 50:
            radius_km = 50
        
        bins_with_distance = []
        
        if user_lat and user_lon:
            try:
                user_lat = float(user_lat)
                user_lon = float(user_lon)
                
                # Calculate distance for each bin
                for bin_location in queryset:
                    distance = bin_location.distance_to(user_lat, user_lon)
                    if distance <= radius_km:
                        bins_with_distance.append({
                            'bin': bin_location,
                            'distance': distance
                        })
                
                # Sort by distance
                bins_with_distance.sort(key=lambda x: x['distance'])
                
                # Serialize with distance context
                serializer = self.get_serializer(
                    [item['bin'] for item in bins_with_distance],
                    many=True,
                    context={
                        'user_latitude': user_lat,
                        'user_longitude': user_lon
                    }
                )
                
                return Response({
                    'count': len(serializer.data),
                    'user_location': {
                        'latitude': user_lat,
                        'longitude': user_lon
                    },
                    'radius_km': radius_km,
                    'bins': serializer.data
                })
                
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid coordinates: {e}")
                return Response(
                    {'error': 'Invalid latitude or longitude values'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # No location provided, return all bins
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'bins': serializer.data
            })


class BinLocationDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for bin location details.
    
    GET /api/bins/{bin_id}
    
    Returns complete bin information.
    """
    
    serializer_class = BinLocationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'bin_id'
    
    def get_queryset(self):
        """Get queryset."""
        return BinLocation.objects.filter(is_active=True)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve bin details with optional distance."""
        instance = self.get_object()
        
        # Get user location for distance calculation
        user_lat = request.query_params.get('latitude')
        user_lon = request.query_params.get('longitude')
        
        context = {}
        if user_lat and user_lon:
            try:
                context['user_latitude'] = float(user_lat)
                context['user_longitude'] = float(user_lon)
            except (ValueError, TypeError):
                pass
        
        serializer = self.get_serializer(instance, context=context)
        return Response(serializer.data)
