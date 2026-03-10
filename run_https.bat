@echo off
echo ========================================
echo GCMS - HTTPS Development Server
echo ========================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call venv\Scripts\activate
)

echo Installing/updating dependencies...
pip install django-extensions pyOpenSSL Werkzeug

echo.
echo Starting HTTPS development server...
echo.
echo Server will be available at:
echo   - Desktop: https://localhost:8000
echo   - Mobile: https://YOUR_IP:8000
echo.
echo To find your IP address, open another terminal and run: ipconfig
echo Look for "IPv4 Address" (usually starts with 192.168.x.x)
echo.
echo IMPORTANT: On mobile, you'll see a certificate warning.
echo Click "Advanced" and "Proceed" to continue (safe for development).
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 0.0.0.0:8000
