from django.urls import path
from . import api_views

urlpatterns = [
    path('create/', api_views.CreatePickupRequestAPIView.as_view(), name='pickups_api_create'),
    path('my/', api_views.MyPickupRequestsAPIView.as_view(), name='pickups_api_my'),
    path('<str:request_id>/', api_views.PickupRequestDetailAPIView.as_view(), name='pickups_api_detail'),
]
