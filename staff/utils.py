"""
Utility functions for staff location tracking and ETA calculation.
"""
import math
from decimal import Decimal


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1: Latitude of first point (decimal degrees)
        lon1: Longitude of first point (decimal degrees)
        lat2: Latitude of second point (decimal degrees)
        lon2: Longitude of second point (decimal degrees)
    
    Returns:
        Distance in kilometers (float)
    """
    # Convert to float if Decimal
    if isinstance(lat1, Decimal):
        lat1 = float(lat1)
    if isinstance(lon1, Decimal):
        lon1 = float(lon1)
    if isinstance(lat2, Decimal):
        lat2 = float(lat2)
    if isinstance(lon2, Decimal):
        lon2 = float(lon2)
    
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def calculate_eta(distance_km, average_speed_kmh=30):
    """
    Calculate estimated time of arrival based on distance.
    
    Args:
        distance_km: Distance in kilometers (float)
        average_speed_kmh: Average travel speed in km/h (default: 30 km/h for urban areas)
    
    Returns:
        ETA in minutes (int)
    """
    if distance_km <= 0:
        return 0
    
    # Calculate time in hours
    time_hours = distance_km / average_speed_kmh
    
    # Convert to minutes and round up
    time_minutes = math.ceil(time_hours * 60)
    
    return time_minutes


def get_staff_eta_to_complaint(staff_member, complaint):
    """
    Calculate ETA for a staff member to reach a complaint location.
    
    Args:
        staff_member: StaffMember instance
        complaint: Complaint instance
    
    Returns:
        dict with distance_km and eta_minutes, or None if location data missing
    """
    # Check if staff has current location
    if not staff_member.current_latitude or not staff_member.current_longitude:
        return None
    
    # Check if complaint has location
    if not complaint.latitude or not complaint.longitude:
        return None
    
    # Calculate distance
    distance = calculate_distance(
        staff_member.current_latitude,
        staff_member.current_longitude,
        complaint.latitude,
        complaint.longitude
    )
    
    # Calculate ETA
    eta = calculate_eta(distance)
    
    return {
        'distance_km': round(distance, 2),
        'eta_minutes': eta
    }
