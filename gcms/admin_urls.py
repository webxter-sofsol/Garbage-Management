from django.urls import path
from staff import views as staff_views

urlpatterns = [
    path('', staff_views.admin_dashboard_view, name='admin_dashboard'),
    path('users/', staff_views.user_list_view, name='admin_users'),
    path('users/<int:user_id>/toggle/', staff_views.user_toggle_view, name='admin_user_toggle'),
]
