from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from complaints.models import Complaint


@login_required
def tracking_map_view(request):
    """
    Real-time staff location tracking map view.
    Only accessible to authorities.
    """
    if not request.user.is_authority:
        return HttpResponseForbidden("Only authorities can access this page.")
    
    return render(request, 'staff/tracking_map.html')


@login_required
def my_assignments_view(request):
    """
    View for staff members to see their assigned complaints.
    """
    if not request.user.is_staff_member:
        return HttpResponseForbidden("Only staff members can access this page.")
    
    # Get staff profile
    try:
        staff_profile = request.user.staff_profile
    except:
        messages.error(request, "Staff profile not found.")
        return redirect('home')
    
    # Get assigned complaints
    complaints = Complaint.objects.filter(
        assigned_staff=staff_profile
    ).select_related('citizen').prefetch_related('photos').order_by('-created_at')
    
    context = {
        'complaints': complaints,
        'staff_profile': staff_profile,
    }
    
    return render(request, 'staff/my_assignments.html', context)


@login_required
def resolve_complaint_view(request, complaint_id):
    """
    View for staff members to resolve complaints.
    """
    if not request.user.is_staff_member:
        return HttpResponseForbidden("Only staff members can access this page.")
    
    # Get staff profile
    try:
        staff_profile = request.user.staff_profile
    except:
        messages.error(request, "Staff profile not found.")
        return redirect('home')
    
    # Get complaint
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id)
    
    # Check if staff member is assigned to this complaint
    if complaint.assigned_staff != staff_profile:
        messages.error(request, "You are not assigned to this complaint.")
        return redirect('staff:my_assignments')
    
    # Get before photos
    before_photos = complaint.photos.filter(photo_type='before')
    
    context = {
        'complaint': complaint,
        'before_photos': before_photos,
    }
    
    return render(request, 'staff/resolve_complaint.html', context)

