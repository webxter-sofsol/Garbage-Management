# Quick Start - HTTPS for Mobile Testing

## Problem
Mobile browsers require HTTPS to access GPS location. HTTP won't work on mobile devices.

## Solution (Choose One)

### Option 1: Self-Signed Certificate (Recommended for Local Network)

**Step 1**: Install dependencies
```bash
pip install django-extensions pyOpenSSL Werkzeug
```

**Step 2**: Run the HTTPS server
```bash
# Windows
run_https.bat

# Linux/Mac
chmod +x run_https.sh
./run_https.sh
```

**Step 3**: Find your computer's IP address
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```
Look for IPv4 address (e.g., 192.168.1.100)

**Step 4**: Access from mobile
1. Make sure mobile is on the **same WiFi** as your computer
2. Open browser on mobile: `https://YOUR_IP:8000`
3. You'll see a security warning - **this is normal**
4. Click "Advanced" → "Proceed to YOUR_IP (unsafe)"
5. Now GPS will work!

---

### Option 2: ngrok (Easiest - Works from Anywhere)

**Step 1**: Download ngrok
- Go to: https://ngrok.com/download
- Create free account
- Download and extract ngrok

**Step 2**: Run Django normally
```bash
python manage.py runserver 8000
```

**Step 3**: In another terminal, run ngrok
```bash
ngrok http 8000
```

**Step 4**: Use the HTTPS URL
- ngrok will show a URL like: `https://abc123.ngrok.io`
- Open this URL on your mobile device
- GPS will work immediately (ngrok provides valid SSL)

**Pros**: 
- No certificate warnings
- Works from any network (not just local WiFi)
- Valid SSL certificate

**Cons**: 
- URL changes every time you restart ngrok
- Free tier has connection limits

---

## Testing GPS on Mobile

1. Open the complaint form: `https://YOUR_URL/complaints/create/`
2. Click "Get Current Location"
3. Browser will ask for location permission - **Allow it**
4. You should see your address appear
5. Submit a complaint to test the full flow

## Troubleshooting

**"Can't connect" on mobile**
- Check both devices are on same WiFi (Option 1)
- Check firewall isn't blocking port 8000
- Try ngrok instead (Option 2)

**"Location access denied"**
- Check browser location permissions
- Make sure you're using HTTPS (not HTTP)
- Try a different browser

**Certificate warning won't go away**
- This is normal for self-signed certificates
- Just click "Advanced" and "Proceed"
- Or use ngrok for no warnings

## Which Option Should I Use?

- **Local testing only**: Use Option 1 (self-signed certificate)
- **Need to test from different networks**: Use Option 2 (ngrok)
- **Want to show someone remotely**: Use Option 2 (ngrok)
- **Production**: Use proper SSL certificate (Let's Encrypt, Cloudflare, etc.)
