from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('tracking-map/', views.tracking_map_view, name='tracking_map'),
    path('my-assignments/', views.my_assignments_view, name='my_assignments'),
    path('resolve/<str:complaint_id>/', views.resolve_complaint_view, name='resolve_complaint'),
]
