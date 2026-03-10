"""
WebSocket routing for staff location tracking.
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/staff/location/', consumers.LocationConsumer.as_asgi()),
]
