# HTTPS Development Setup for GCMS

## Why HTTPS is Required

Modern browsers require HTTPS for accessing sensitive APIs like:
- Geolocation API (GPS location)
- Camera/Microphone access
- Service Workers
- Push Notifications

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `django-extensions` - Provides `runserver_plus` with SSL support
- `pyOpenSSL` - SSL certificate handling
- `Werkzeug` - Development server with SSL

### 2. Generate Self-Signed Certificate

Run this command to generate a self-signed SSL certificate:

```bash
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 0.0.0.0:8000
```

On first run, it will automatically generate `cert.pem` and `key.pem` files.

### 3. Run Development Server with HTTPS

```bash
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 0.0.0.0:8000
```

The server will be available at:
- **Desktop**: https://localhost:8000
- **Mobile (same network)**: https://YOUR_IP:8000

### 4. Find Your Local IP Address

**Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" under your active network adapter (usually starts with 192.168.x.x)

**Linux/Mac:**
```bash
ifconfig
```
or
```bash
ip addr show
```

### 5. Access from Mobile Device

1. Make sure your mobile device is on the **same WiFi network** as your computer
2. Open browser on mobile and go to: `https://YOUR_IP:8000`
3. You'll see a security warning (because it's a self-signed certificate)
4. **Accept the certificate warning** (this is safe for development)
   - Chrome: Click "Advanced" → "Proceed to YOUR_IP (unsafe)"
   - Safari: Click "Show Details" → "visit this website"
   - Firefox: Click "Advanced" → "Accept the Risk and Continue"

### 6. Trust the Certificate (Optional - Better UX)

#### On Android:
1. Download the `cert.pem` file to your phone
2. Go to Settings → Security → Install from storage
3. Select the certificate file
4. Give it a name and select "VPN and apps"

#### On iOS:
1. Email yourself the `cert.pem` file or host it temporarily
2. Open the file on your iPhone
3. Go to Settings → General → Profile
4. Install the profile
5. Go to Settings → General → About → Certificate Trust Settings
6. Enable full trust for the certificate

## Alternative: Use ngrok (Easier for Mobile Testing)

If you don't want to deal with certificates, use ngrok:

### 1. Install ngrok
Download from: https://ngrok.com/download

### 2. Run Django normally
```bash
python manage.py runserver 8000
```

### 3. In another terminal, run ngrok
```bash
ngrok http 8000
```

### 4. Use the HTTPS URL
ngrok will give you a public HTTPS URL like: `https://abc123.ngrok.io`
Use this URL on your mobile device - it already has a valid SSL certificate!

**Note**: Free ngrok URLs change every time you restart ngrok.

## Troubleshooting

### "Connection refused" on mobile
- Check firewall settings on your computer
- Make sure both devices are on the same WiFi network
- Try disabling Windows Firewall temporarily for testing

### "Certificate error" persists
- Clear browser cache on mobile
- Try a different browser
- Use ngrok instead

### Geolocation still not working
- Make sure you're using HTTPS (not HTTP)
- Check browser console for errors
- Ensure location permissions are enabled in browser settings

## Production Deployment

For production, use a proper SSL certificate from:
- Let's Encrypt (free)
- Cloudflare (free)
- Commercial SSL providers

Never use self-signed certificates in production!
