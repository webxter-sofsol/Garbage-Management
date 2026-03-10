from django.urls import path
from . import api_views

urlpatterns = [
    path('list/', api_views.ComplaintListAPIView.as_view(), name='complaints_api_list'),
    path('<str:complaint_id>/', api_views.ComplaintDetailAPIView.as_view(), name='complaints_api_detail'),
    path('<str:complaint_id>/assign/', api_views.AssignStaffAPIView.as_view(), name='complaints_api_assign'),
    path('<str:complaint_id>/resolve/', api_views.ResolveComplaintAPIView.as_view(), name='complaints_api_resolve'),
]
