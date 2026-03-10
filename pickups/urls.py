from django.urls import path
from . import views

app_name = 'pickups'

urlpatterns = [
    path('create/', views.CreatePickupRequestView.as_view(), name='create'),
    path('my/', views.MyPickupRequestsView.as_view(), name='my_requests'),
    path('<str:request_id>/', views.PickupRequestDetailView.as_view(), name='detail'),
]
