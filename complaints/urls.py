from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('create/', views.CreateComplaintView.as_view(), name='create'),
    path('my/', views.MyComplaintsView.as_view(), name='my_complaints'),
    path('dashboard/', views.AuthorityDashboardView.as_view(), name='authority_dashboard'),
    path('<str:complaint_id>/', views.ComplaintDetailView.as_view(), name='detail'),
]
