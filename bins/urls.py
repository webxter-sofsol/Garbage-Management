from django.urls import path
from . import views

app_name = 'bins'

urlpatterns = [
    path('map/', views.BinMapView.as_view(), name='map'),
    path('<str:bin_id>/', views.BinDetailView.as_view(), name='detail'),
]
