from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q
import secrets
import string

from complaints.models import Complaint
from authentication.models import User
from .models import StaffMember


# ---------------------------------------------------------------------------
# Existing staff-member views
# ---------------------------------------------------------------------------

@login_required
def tracking_map_view(request):
    """Real-time staff location tracking map view. Authority only."""
    if not request.user.is_authority:
        return HttpResponseForbidden("Only authorities can access this page.")
    return render(request, 'staff/tracking_map.html')


@login_required
def my_assignments_view(request):
    """Staff members see their assigned complaints."""
    if not request.user.is_staff_member:
        return HttpResponseForbidden("Only staff members can access this page.")

    try:
        staff_profile = request.user.staff_profile
    except Exception:
        messages.error(request, "Staff profile not found.")
        return redirect('home')

    complaints = Complaint.objects.filter(
        assigned_staff=staff_profile
    ).select_related('citizen').prefetch_related('photos').order_by('-created_at')

    return render(request, 'staff/my_assignments.html', {
        'complaints': complaints,
        'staff_profile': staff_profile,
    })


@login_required
def resolve_complaint_view(request, complaint_id):
    """Staff members resolve complaints."""
    if not request.user.is_staff_member:
        return HttpResponseForbidden("Only staff members can access this page.")

    try:
        staff_profile = request.user.staff_profile
    except Exception:
        messages.error(request, "Staff profile not found.")
        return redirect('home')

    complaint = get_object_or_404(Complaint, complaint_id=complaint_id)

    if complaint.assigned_staff != staff_profile:
        messages.error(request, "You are not assigned to this complaint.")
        return redirect('staff:my_assignments')

    before_photos = complaint.photos.filter(photo_type='before')

    return render(request, 'staff/resolve_complaint.html', {
        'complaint': complaint,
        'before_photos': before_photos,
    })


# ---------------------------------------------------------------------------
# Staff management views (authority only)
# ---------------------------------------------------------------------------

def _authority_required(request):
    """Return redirect response if user is not authority, else None."""
    if not request.user.is_authenticated or not request.user.is_authority:
        return redirect('home')
    return None


@login_required
def staff_list_view(request):
    """List all StaffMember objects with optional search."""
    guard = _authority_required(request)
    if guard:
        return guard

    search_query = request.GET.get('q', '').strip()
    staff_members = StaffMember.objects.select_related('user').all()

    if search_query:
        staff_members = staff_members.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(staff_id__icontains=search_query)
        )

    return render(request, 'staff/manage/list.html', {
        'staff_members': staff_members,
        'search_query': search_query,
    })


@login_required
def staff_create_view(request):
    """Create a new User + StaffMember."""
    guard = _authority_required(request)
    if guard:
        return guard

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        duty_status = request.POST.get('duty_status', 'off_duty')

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        elif User.objects.filter(email=email).exists():
            errors.append("A user with this email already exists.")
        if not phone:
            errors.append("Phone is required.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'staff/manage/create.html', {
                'form_data': request.POST,
            })

        # Generate a random password (staff use OTP to login)
        alphabet = string.ascii_letters + string.digits
        random_password = ''.join(secrets.choice(alphabet) for _ in range(20))

        user = User.objects.create_user(
            email=email,
            password=random_password,
            is_staff_member=True,
            is_citizen=False,
        )

        StaffMember.objects.create(
            user=user,
            name=name,
            phone=phone,
            duty_status=duty_status,
        )

        messages.success(request, f"Staff member '{name}' created successfully.")
        return redirect('staff:staff_list')

    return render(request, 'staff/manage/create.html', {'form_data': {}})


@login_required
def staff_detail_view(request, staff_id):
    """Show staff details and their active assigned complaints."""
    guard = _authority_required(request)
    if guard:
        return guard

    staff_member = get_object_or_404(StaffMember, staff_id=staff_id)
    assigned_complaints = Complaint.objects.filter(
        assigned_staff=staff_member,
        status__in=['assigned', 'in-progress']
    ).order_by('-created_at')

    return render(request, 'staff/manage/detail.html', {
        'staff_member': staff_member,
        'assigned_complaints': assigned_complaints,
    })


@login_required
def staff_edit_view(request, staff_id):
    """Edit a staff member's details."""
    guard = _authority_required(request)
    if guard:
        return guard

    staff_member = get_object_or_404(StaffMember, staff_id=staff_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        duty_status = request.POST.get('duty_status', staff_member.duty_status)
        is_active = request.POST.get('is_active') == 'on'

        if not name:
            messages.error(request, "Name is required.")
            return render(request, 'staff/manage/edit.html', {'staff_member': staff_member})
        if not phone:
            messages.error(request, "Phone is required.")
            return render(request, 'staff/manage/edit.html', {'staff_member': staff_member})

        staff_member.name = name
        staff_member.phone = phone
        staff_member.duty_status = duty_status
        staff_member.is_active = is_active
        staff_member.save()

        messages.success(request, "Staff member updated successfully.")
        return redirect('staff:staff_detail', staff_id=staff_id)

    return render(request, 'staff/manage/edit.html', {'staff_member': staff_member})


@login_required
def staff_toggle_duty_view(request, staff_id):
    """Toggle duty_status between on_duty and off_duty (POST only)."""
    guard = _authority_required(request)
    if guard:
        return guard

    if request.method != 'POST':
        return redirect('staff:staff_detail', staff_id=staff_id)

    staff_member = get_object_or_404(StaffMember, staff_id=staff_id)

    if staff_member.duty_status == 'on_duty':
        staff_member.duty_status = 'off_duty'
    else:
        staff_member.duty_status = 'on_duty'
    staff_member.save(update_fields=['duty_status'])

    messages.success(request, f"Duty status updated to {staff_member.get_duty_status_display()}.")
    return redirect('staff:staff_detail', staff_id=staff_id)


# ---------------------------------------------------------------------------
# Admin panel views (authority only)
# ---------------------------------------------------------------------------

@login_required
def admin_dashboard_view(request):
    """System overview stats for the admin panel."""
    guard = _authority_required(request)
    if guard:
        return guard

    total_users = User.objects.count()
    total_staff = StaffMember.objects.count()
    total_complaints = Complaint.objects.count()
    pending_complaints = Complaint.objects.filter(status='pending').count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()
    staff_on_duty = StaffMember.objects.filter(duty_status='on_duty').count()
    recent_complaints = Complaint.objects.select_related('citizen').order_by('-created_at')[:5]

    return render(request, 'admin/dashboard.html', {
        'total_users': total_users,
        'total_staff': total_staff,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'resolved_complaints': resolved_complaints,
        'staff_on_duty': staff_on_duty,
        'recent_complaints': recent_complaints,
    })


@login_required
def user_list_view(request):
    """List all users with search and type filter."""
    guard = _authority_required(request)
    if guard:
        return guard

    search_query = request.GET.get('q', '').strip()
    user_type_filter = request.GET.get('type', '').strip()

    users = User.objects.all().order_by('-created_at')

    if search_query:
        users = users.filter(email__icontains=search_query)

    if user_type_filter == 'citizen':
        users = users.filter(is_citizen=True, is_authority=False, is_staff_member=False)
    elif user_type_filter == 'authority':
        users = users.filter(is_authority=True)
    elif user_type_filter == 'staff_member':
        users = users.filter(is_staff_member=True)

    return render(request, 'admin/users.html', {
        'users': users,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
    })


@login_required
def user_toggle_view(request, user_id):
    """Toggle a user's is_active status (POST only)."""
    guard = _authority_required(request)
    if guard:
        return guard

    if request.method != 'POST':
        return redirect('admin_users')

    user = get_object_or_404(User, pk=user_id)

    # Prevent authority from deactivating themselves
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('admin_users')

    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])

    status_text = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.email} has been {status_text}.")
    return redirect('admin_users')
