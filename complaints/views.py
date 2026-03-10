from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from datetime import datetime
from .models import Complaint, ComplaintPhoto
from .validators import ComplaintValidator
import logging

logger = logging.getLogger(__name__)


@method_decorator([login_required, csrf_protect], name='dispatch')
class CreateComplaintView(View):
    """View for creating a new complaint."""
    
    template_name = 'complaints/create.html'
    
    def get(self, request):
        """Display complaint creation form."""
        return render(request, self.template_name)
    
    def post(self, request):
        """Process complaint submission."""
        # Get form data
        description = request.POST.get('description', '').strip()
        latitude = request.POST.get('latitude', '')
        longitude = request.POST.get('longitude', '')
        address = request.POST.get('address', '').strip()
        photos = request.FILES.getlist('photos')
        
        # Validate data
        is_valid, errors = ComplaintValidator.validate_complaint_data(
            description, latitude, longitude, photos
        )
        
        if not is_valid:
            for field, error in errors.items():
                messages.error(request, f"{field.title()}: {error}")
            return render(request, self.template_name, {
                'description': description,
                'latitude': latitude,
                'longitude': longitude,
            })
        
        try:
            # Create complaint
            complaint = Complaint.objects.create(
                citizen=request.user,
                description=description,
                latitude=float(latitude),
                longitude=float(longitude),
                address=address if address else None,
                status='pending'
            )
            
            # Save photos
            for photo in photos:
                ComplaintPhoto.objects.create(
                    complaint=complaint,
                    photo=photo,
                    photo_type='before'
                )
            
            logger.info(f"Complaint {complaint.complaint_id} created by {request.user.email}")
            messages.success(request, f"Complaint submitted successfully! ID: {complaint.complaint_id}")
            return redirect('complaints:detail', complaint_id=complaint.complaint_id)
            
        except Exception as e:
            logger.error(f"Error creating complaint: {str(e)}")
            messages.error(request, "An error occurred while submitting your complaint. Please try again.")
            return render(request, self.template_name, {
                'description': description,
                'latitude': latitude,
                'longitude': longitude,
            })


@method_decorator(login_required, name='dispatch')
class ComplaintDetailView(View):
    """View for displaying complaint details."""
    
    template_name = 'complaints/detail.html'
    
    def get(self, request, complaint_id):
        """Display complaint details."""
        complaint = get_object_or_404(Complaint, complaint_id=complaint_id)
        
        # Check if user has permission to view
        if not (request.user == complaint.citizen or 
                request.user.is_authority or 
                request.user.is_staff_member):
            messages.error(request, "You don't have permission to view this complaint.")
            return redirect('home')
        
        context = {
            'complaint': complaint,
            'photos': complaint.photos.all(),
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class MyComplaintsView(View):
    """View for displaying user's complaints."""
    
    template_name = 'complaints/my_complaints.html'
    
    def get(self, request):
        """Display user's complaints."""
        complaints = Complaint.objects.filter(citizen=request.user).order_by('-created_at')
        
        context = {
            'complaints': complaints,
        }
        return render(request, self.template_name, context)



@method_decorator(login_required, name='dispatch')
class AuthorityDashboardView(View):
    """View for authority complaint dashboard with filtering and sorting."""
    
    template_name = 'complaints/authority_dashboard.html'
    
    def get(self, request):
        """Display complaint dashboard with filters."""
        # Check if user is authority
        if not request.user.is_authority:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('home')
        
        # Get base queryset
        complaints = Complaint.objects.select_related('citizen', 'assigned_staff').all()
        
        # Apply filters
        status_filter = request.GET.get('status', '')
        if status_filter:
            complaints = complaints.filter(status=status_filter)
        
        date_from = request.GET.get('date_from', '')
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                complaints = complaints.filter(created_at__gte=date_from_obj)
            except ValueError:
                messages.warning(request, "Invalid 'from' date format.")
        
        date_to = request.GET.get('date_to', '')
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                complaints = complaints.filter(created_at__lte=date_to_obj)
            except ValueError:
                messages.warning(request, "Invalid 'to' date format.")
        
        search = request.GET.get('search', '')
        if search:
            complaints = complaints.filter(
                Q(complaint_id__icontains=search) |
                Q(description__icontains=search) |
                Q(address__icontains=search)
            )
        
        # Apply sorting
        ordering = request.GET.get('ordering', '-created_at')
        complaints = complaints.order_by(ordering)
        
        # Calculate stats
        all_complaints = Complaint.objects.all()
        stats = {
            'total': all_complaints.count(),
            'pending': all_complaints.filter(status='pending').count(),
            'assigned': all_complaints.filter(status='assigned').count(),
            'resolved': all_complaints.filter(status='resolved').count(),
        }
        
        # Pagination
        paginator = Paginator(complaints, 10)  # 10 complaints per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'complaints': page_obj,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'stats': stats,
        }
        
        return render(request, self.template_name, context)
