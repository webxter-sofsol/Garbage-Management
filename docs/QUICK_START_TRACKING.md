# Quick Start: Real-time Location Tracking

## Prerequisites

1. Django project is set up and running
2. Redis is installed and running
3. All dependencies from `requirements.txt` are installed

## Step 1: Start Redis Server

### Windows
```bash
# Download Redis from: https://github.com/microsoftarchive/redis/releases
# Extract and run:
redis-server.exe
```

### Linux/macOS
```bash
# Install Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                  # macOS

# Start Redis
redis-server
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

## Step 2: Run Django with ASGI

The real-time tracking uses WebSockets, which require running Django with ASGI support.

### Development Server

For development, you can use Django's built-in ASGI server:

```bash
python manage.py runserver
```

Django 5.x automatically supports both HTTP and WebSocket connections.

### Production Server (Daphne)

For production, use Daphne (ASGI server):

```bash
# Install Daphne
pip install daphne

# Run with Daphne
daphne -b 0.0.0.0 -p 8000 gcms.asgi:application
```

## Step 3: Access the Tracking Map

1. Log in as an authority user
2. Navigate to: `http://localhost:8000/staff/tracking-map/`
3. You should see an interactive map

## Step 4: Test Location Updates

### Option A: Using WebSocket Test Client

Create a test file `test_websocket.py`:

```python
import asyncio
import websockets
import json

async def send_location():
    uri = "ws://localhost:8000/ws/staff/location/"
    
    async with websockets.connect(uri) as websocket:
        # Send location update
        message = {
            "staff_id": "STF-001",  # Use a valid staff ID from your database
            "latitude": 40.7128,
            "longitude": -74.0060,
            "timestamp": "2024-01-15T10:30:00Z",
            "accuracy": 10.5
        }
        
        await websocket.send(json.dumps(message))
        
        # Receive response
        response = await websocket.recv()
        print(f"Response: {response}")

# Run the test
asyncio.run(send_location())
```

Run it:
```bash
pip install websockets
python test_websocket.py
```

### Option B: Using Browser Console

Open the tracking map in your browser and use the console:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/staff/location/');

ws.onopen = () => {
    console.log('Connected!');
    
    // Send location update
    ws.send(JSON.stringify({
        staff_id: 'STF-001',  // Use a valid staff ID
        latitude: 40.7128,
        longitude: -74.0060,
        timestamp: new Date().toISOString(),
        accuracy: 10.5
    }));
};

ws.onmessage = (event) => {
    console.log('Response:', JSON.parse(event.data));
};
```

### Option C: Using curl to test API endpoint

Test the REST API endpoint:

```bash
# Get active staff locations
curl -X GET http://localhost:8000/api/staff/active-locations/ \
  -H "Content-Type: application/json" \
  --cookie "sessionid=YOUR_SESSION_ID"
```

## Step 5: Create Test Staff Member

If you don't have a staff member yet:

```bash
python manage.py shell
```

```python
from authentication.models import User
from staff.models import StaffMember

# Create staff user
user = User.objects.create(
    email='staff@test.com',
    is_staff_member=True
)
user.set_password('password123')
user.save()

# Create staff member
staff = StaffMember.objects.create(
    user=user,
    name='Test Staff',
    phone='+1234567890',
    duty_status='on_duty'
)

print(f"Created staff member: {staff.staff_id}")
```

## Troubleshooting

### Issue: WebSocket connection refused

**Solution**: Make sure Redis is running
```bash
redis-cli ping
```

### Issue: "Staff member is not on duty" error

**Solution**: Update staff duty status
```python
from staff.models import StaffMember
staff = StaffMember.objects.get(staff_id='STF-001')
staff.duty_status = 'on_duty'
staff.save()
```

### Issue: "Location updates must be at least 30 seconds apart"

**Solution**: Wait 30 seconds between location updates or update the last_location_update timestamp:
```python
from staff.models import StaffMember
from django.utils import timezone
from datetime import timedelta

staff = StaffMember.objects.get(staff_id='STF-001')
staff.last_location_update = timezone.now() - timedelta(minutes=5)
staff.save()
```

### Issue: Map not showing staff locations

**Checklist**:
1. Staff duty_status is 'on_duty' or 'on_break'
2. Staff has current_latitude and current_longitude set
3. last_location_update is within last 5 minutes
4. Check browser console for JavaScript errors
5. Verify API endpoint returns data: `/api/staff/active-locations/`

## Next Steps

1. **Mobile App Integration**: Implement location tracking in staff mobile app
2. **Complaint Assignment**: Use staff locations for intelligent complaint assignment
3. **Route Optimization**: Optimize collection routes based on real-time locations
4. **Notifications**: Set up alerts for staff entering/leaving areas

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ws/staff/location/` | WebSocket | Send real-time location updates |
| `/api/staff/active-locations/` | GET | Get all on-duty staff locations |
| `/staff/tracking-map/` | GET | View tracking map interface |

## Configuration

All configuration is in `gcms/settings.py`:

```python
# Redis configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get("REDIS_HOST", "127.0.0.1"), 6379)],
        },
    },
}
```

To use a different Redis host:
```bash
export REDIS_HOST=your-redis-host
```

## Performance Tips

1. **Location Update Frequency**: Send updates every 30 seconds (enforced minimum)
2. **Batch Updates**: If tracking multiple staff, consider batching API calls
3. **Map Refresh**: Default 30-second auto-refresh is optimal for most use cases
4. **Redis Memory**: Monitor Redis memory usage with `redis-cli info memory`

## Security Notes

1. WebSocket connections should use WSS (secure WebSocket) in production
2. Implement proper authentication for WebSocket connections
3. Validate all incoming location data
4. Rate limit location updates per staff member
5. Use HTTPS for all API endpoints in production
