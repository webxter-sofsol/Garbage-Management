from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from .models import PickupRequest
from .validators import PickupRequestValidator
import logging

logger = logging.getLogger(__name__)


@method_decorator([login_required, csrf_protect], name='dispatch')
class CreatePickupRequestView(View):
    """View for creating a new pickup request."""
    
    template_name = 'pickups/create.html'
    
    def get(self, request):
        """Display pickup request creation form."""
        return render(request, self.template_name)
    
    def post(self, request):
        """Process pickup request submission."""
        # Get form data
        waste_type = request.POST.get('waste_type', '')
        preferred_date = request.POST.get('preferred_date', '')
        preferred_time = request.POST.get('preferred_time', '')
        latitude = request.POST.get('latitude', '')
        longitude = request.POST.get('longitude', '')
        address = request.POST.get('address', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validate data
        is_valid, errors = PickupRequestValidator.validate_pickup_request_data(
            waste_type, preferred_date, latitude, longitude, address, notes
        )
        
        if not is_valid:
            for field, error in errors.items():
                messages.error(request, f"{field.title()}: {error}")
            return render(request, self.template_name, {
                'waste_type': waste_type,
                'preferred_date': preferred_date,
                'preferred_time': preferred_time,
                'latitude': latitude,
                'longitude': longitude,
                'address': address,
                'notes': notes,
            })
        
        try:
            # Create pickup request
            pickup_request = PickupRequest.objects.create(
                citizen=request.user,
                waste_type=waste_type,
                preferred_date=preferred_date,
                preferred_time=preferred_time if preferred_time else None,
                latitude=float(latitude),
                longitude=float(longitude),
                address=address,
                notes=notes if notes else None,
                status='pending'
            )
            
            logger.info(f"Pickup request {pickup_request.request_id} created by {request.user.email}")
            messages.success(request, f"Pickup request submitted successfully! ID: {pickup_request.request_id}")
            return redirect('pickups:detail', request_id=pickup_request.request_id)
            
        except Exception as e:
            logger.error(f"Error creating pickup request: {str(e)}")
            messages.error(request, "An error occurred while submitting your request. Please try again.")
            return render(request, self.template_name, {
                'waste_type': waste_type,
                'preferred_date': preferred_date,
                'preferred_time': preferred_time,
                'latitude': latitude,
                'longitude': longitude,
                'address': address,
                'notes': notes,
            })


@method_decorator(login_required, name='dispatch')
class PickupRequestDetailView(View):
    """View for displaying pickup request details."""
    
    template_name = 'pickups/detail.html'
    
    def get(self, request, request_id):
        """Display pickup request details."""
        pickup_request = get_object_or_404(PickupRequest, request_id=request_id)
        
        # Check if user has permission to view
        if not (request.user == pickup_request.citizen or 
                request.user.is_authority or 
                request.user.is_staff_member):
            messages.error(request, "You don't have permission to view this pickup request.")
            return redirect('home')
        
        context = {
            'pickup_request': pickup_request,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class MyPickupRequestsView(View):
    """View for displaying user's pickup requests."""
    
    template_name = 'pickups/my_requests.html'
    
    def get(self, request):
        """Display user's pickup requests."""
        pickup_requests = PickupRequest.objects.filter(citizen=request.user).order_by('-created_at')
        
        context = {
            'pickup_requests': pickup_requests,
        }
        return render(request, self.template_name, context)
