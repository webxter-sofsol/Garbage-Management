from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('tracking-map/', views.tracking_map_view, name='tracking_map'),
    path('my-assignments/', views.my_assignments_view, name='my_assignments'),
    path('resolve/<str:complaint_id>/', views.resolve_complaint_view, name='resolve_complaint'),
    # Staff management (authority only)
    path('manage/', views.staff_list_view, name='staff_list'),
    path('manage/create/', views.staff_create_view, name='staff_create'),
    path('manage/<str:staff_id>/', views.staff_detail_view, name='staff_detail'),
    path('manage/<str:staff_id>/edit/', views.staff_edit_view, name='staff_edit'),
    path('manage/<str:staff_id>/toggle-duty/', views.staff_toggle_duty_view, name='staff_toggle_duty'),
]
