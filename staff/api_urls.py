from django.urls import path
from . import api_views

urlpatterns = [
    path('list/', api_views.StaffListAPIView.as_view(), name='staff_api_list'),
    path('active-locations/', api_views.ActiveStaffLocationsAPIView.as_view(), name='staff_active_locations'),
]
