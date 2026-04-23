from django.urls import path
from . import api_views

urlpatterns = [
    path('nearby/', api_views.BinLocationListAPIView.as_view(), name='bins_api_nearby'),
    path('<str:bin_id>/', api_views.BinLocationDetailAPIView.as_view(), name='bins_api_detail'),
]
