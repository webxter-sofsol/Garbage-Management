# Real-time Location Tracking System

## Overview

The Real-time Location Tracking Module enables authorities to monitor collection staff locations in real-time through WebSocket connections and an interactive map interface.

## Features

1. **WebSocket-based Location Updates**: Staff members send location updates via WebSocket connection
2. **Location History**: All location updates are stored in the database for historical tracking
3. **ETA Calculation**: Automatic calculation of estimated time of arrival to complaint locations
4. **Interactive Map**: Real-time visualization of staff locations with status indicators
5. **Auto-refresh**: Map updates every 30 seconds automatically
6. **Active Staff API**: REST endpoint for retrieving all on-duty staff locations

## Components

### 1. WebSocket Consumer (`staff/consumers.py`)

Handles real-time location updates from staff members.

**Endpoint**: `ws://localhost:8000/ws/staff/location/`

**Message Format**:
```json
{
    "staff_id": "STF-001",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "timestamp": "2024-01-15T10:30:00Z",
    "accuracy": 10.5
}
```

**Validation**:
- Validates staff_id exists
- Checks staff is on duty
- Enforces 30-second minimum interval between updates
- Validates coordinate ranges (-90 to 90 for latitude, -180 to 180 for longitude)

**Response**:
```json
{
    "status": "success",
    "message": "Location updated successfully",
    "staff_id": "STF-001",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Location Utilities (`staff/utils.py`)

**Functions**:

- `calculate_distance(lat1, lon1, lat2, lon2)`: Calculate distance between two coordinates using Haversine formula
- `calculate_eta(distance_km, average_speed_kmh=30)`: Calculate estimated time of arrival in minutes
- `get_staff_eta_to_complaint(staff_member, complaint)`: Get ETA for staff to reach complaint location

### 3. Active Locations API (`/api/staff/active-locations/`)

REST endpoint for retrieving all on-duty staff with current locations.

**Method**: GET

**Authentication**: Required (Authority only)

**Response**:
```json
{
    "count": 5,
    "staff_locations": [
        {
            "staff_id": "STF-001",
            "name": "John Doe",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "status": "on_duty",
            "assigned_complaints": 3,
            "last_update": "2024-01-15T10:30:00Z"
        }
    ]
}
```

**Filters**:
- Only includes staff with `duty_status` of "on_duty" or "on_break"
- Only includes staff with location updates within last 5 minutes
- Only includes active staff members

### 4. Tracking Map UI (`/staff/tracking-map/`)

Interactive map interface for real-time staff tracking.

**Features**:
- Leaflet.js-based interactive map
- Color-coded markers (green for on-duty, yellow for on-break)
- Staff information popups with details
- Active staff count display
- Staff list cards with status and workload
- Auto-refresh every 30 seconds
- Auto-fit map bounds to show all staff

**Access**: Authority users only

## Usage

### For Staff Members (Mobile App/Client)

1. Establish WebSocket connection to `ws://your-domain/ws/staff/location/`
2. Send location updates every 30 seconds while on duty
3. Include staff_id, latitude, longitude in each message
4. Handle success/error responses

**Example JavaScript Client**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/staff/location/');

ws.onopen = () => {
    console.log('Connected to location tracking');
};

// Send location update
function sendLocation(staffId, lat, lon) {
    const message = {
        staff_id: staffId,
        latitude: lat,
        longitude: lon,
        timestamp: new Date().toISOString(),
        accuracy: 10.5
    };
    ws.send(JSON.stringify(message));
}

// Get location from browser
if (navigator.geolocation) {
    setInterval(() => {
        navigator.geolocation.getCurrentPosition((position) => {
            sendLocation(
                'STF-001',
                position.coords.latitude,
                position.coords.longitude
            );
        });
    }, 30000); // Every 30 seconds
}
```

### For Authorities (Web Interface)

1. Navigate to `/staff/tracking-map/`
2. View real-time staff locations on the map
3. Click markers for detailed staff information
4. Monitor active staff count and workload
5. Map auto-refreshes every 30 seconds

## Database Models

### StaffMember
- `current_latitude`: Current latitude coordinate
- `current_longitude`: Current longitude coordinate
- `last_location_update`: Timestamp of last location update
- `duty_status`: Current duty status (on_duty, off_duty, on_break)

### LocationUpdate
- `staff_member`: Foreign key to StaffMember
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate
- `timestamp`: Timestamp of update (auto-generated)
- `accuracy`: GPS accuracy in meters (optional)

## Configuration

### Redis Setup

The WebSocket functionality requires Redis as a channel layer backend.

**Install Redis**:
- Windows: Download from https://github.com/microsoftarchive/redis/releases
- Linux: `sudo apt-get install redis-server`
- macOS: `brew install redis`

**Start Redis**:
```bash
redis-server
```

**Environment Variables** (`.env`):
```
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
```

### Django Settings

Already configured in `gcms/settings.py`:

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get("REDIS_HOST", "127.0.0.1"), 6379)],
        },
    },
}
```

## Testing

Run the test suite:

```bash
python manage.py test staff.tests
```

**Test Coverage**:
- Location update functionality
- Distance calculation (Haversine formula)
- ETA calculation
- Staff workload limits
- Coordinate validation
- Location history tracking

## Performance Considerations

1. **Location Update Frequency**: Enforced 30-second minimum interval to prevent database overload
2. **Stale Location Filtering**: API only returns locations updated within last 5 minutes
3. **Database Indexing**: Indexes on staff_id, duty_status, and location coordinates
4. **Auto-refresh Rate**: UI refreshes every 30 seconds (configurable)

## Security

1. **Authentication Required**: All endpoints require user authentication
2. **Authority-Only Access**: Tracking map and API restricted to authority users
3. **WebSocket Validation**: All incoming messages validated for format and content
4. **Coordinate Range Validation**: Prevents invalid coordinate submissions

## Troubleshooting

### WebSocket Connection Fails
- Ensure Redis is running
- Check REDIS_HOST and REDIS_PORT in settings
- Verify ASGI application is configured correctly

### Location Updates Not Appearing
- Check staff duty_status is "on_duty" or "on_break"
- Verify location updates are at least 30 seconds apart
- Check Redis connection

### Map Not Loading
- Ensure Leaflet.js CDN is accessible
- Check browser console for JavaScript errors
- Verify API endpoint returns data

## Future Enhancements

1. Route optimization based on staff locations
2. Geofencing alerts when staff enters/exits areas
3. Historical route playback
4. Push notifications for location-based events
5. Integration with navigation apps for turn-by-turn directions
