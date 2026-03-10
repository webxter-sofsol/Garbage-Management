# Garbage Collection Management System (GCMS)

A comprehensive web-based platform that connects citizens with municipal waste management authorities for efficient waste management operations.

## Features

- **User Authentication**: Email-based OTP login system
- **Complaint Reporting**: Citizens can report garbage issues with photos and location
- **Staff Management**: Assign and track collection staff
- **Real-time Tracking**: Monitor staff locations via WebSocket
- **Analytics Dashboard**: View metrics, trends, and performance data
- **AI Integration**: Intelligent complaint categorization, route optimization, and predictive analytics
- **Notifications**: Email and push notifications for status updates
- **Mobile Responsive**: Optimized for mobile devices with GPS support

## Technology Stack

- **Backend**: Django 5.2, Python 3.11
- **Database**: SQLite (development), MySQL/PostgreSQL (production)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Real-time**: Django Channels, WebSockets, Redis
- **Background Tasks**: Celery
- **Testing**: pytest, Hypothesis (property-based testing)
- **AI/ML**: scikit-learn, transformers

## Installation

### Prerequisites

- Python 3.11+
- Redis 6.0+ (for WebSockets and Celery)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd GarbageManagement
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

5. Update `.env` with your configuration (email settings, Redis, etc.)

6. Run migrations:
```bash
python manage.py migrate
```

7. Create superuser:
```bash
python manage.py createsuperuser
```

8. Collect static files:
```bash
python manage.py collectstatic
```

## Running the Application

### Development Server (HTTP)

1. Start Django development server:
```bash
python manage.py runserver
```

2. Start Redis server (in separate terminal):
```bash
redis-server
```

3. Start Celery worker (in separate terminal):
```bash
celery -A gcms worker -l info
```

4. Start Celery beat scheduler (in separate terminal):
```bash
celery -A gcms beat -l info
```

Access the application at `http://localhost:8000`

### Development Server with HTTPS (Required for Mobile GPS)

**Important**: Modern browsers require HTTPS for geolocation API access on mobile devices.

1. Install HTTPS dependencies (already in requirements.txt):
```bash
pip install django-extensions pyOpenSSL Werkzeug
```

2. Run server with HTTPS:
```bash
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 0.0.0.0:8000
```

3. Access from mobile:
   - Find your computer's IP address: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
   - On mobile browser: `https://YOUR_IP:8000`
   - Accept the self-signed certificate warning

**For detailed HTTPS setup instructions, see [HTTPS_SETUP.md](HTTPS_SETUP.md)**

**Alternative**: Use ngrok for easier mobile testing with automatic HTTPS:
```bash
# Terminal 1: Run Django
python manage.py runserver 8000

# Terminal 2: Run ngrok
ngrok http 8000
```
Use the ngrok HTTPS URL on your mobile device.

## Testing

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest authentication/tests.py
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

## Project Structure

```
GarbageManagement/
├── authentication/      # User authentication module
├── complaints/          # Complaint management
├── pickups/            # Pickup request scheduling
├── staff/              # Staff management and tracking
├── routes/             # Collection route planning
├── bins/               # Bin location management
├── notifications/      # Notification system
├── analytics/          # Analytics and reporting
├── api/                # REST API endpoints
├── ai_integration/     # AI/ML features
├── gcms/               # Project settings
├── templates/          # HTML templates
├── static/             # Static files (CSS, JS)
├── media/              # User uploaded files
└── logs/               # Application logs
```

## API Documentation

API documentation is available at `/api/docs/` when running the development server.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.
