# 🚀 Quick Start: Share MoodCapture with ngrok

## ⚡ 3-Step Setup (5 minutes)

### Step 1: Install ngrok
```powershell
# Download from https://ngrok.com/download
# Extract ngrok.exe to any folder
```

### Step 2: Get Auth Token
1. Sign up at https://dashboard.ngrok.com/signup (free)
2. Copy your token from https://dashboard.ngrok.com/get-started/your-authtoken
3. Run (replace YOUR_TOKEN):
```powershell
ngrok config add-authtoken YOUR_TOKEN
```

### Step 3: Start Demo
Open 2 terminals:

**Terminal 1 - Start Backend:**
```powershell
cd E:\Vantage_Assignment\MoodCapture
python backend/start_no_reload.py
```

**Terminal 2 - Start ngrok:**
```powershell
ngrok http 8000
```

---

## 🌐 Your Public URL

ngrok will show something like:
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8000
```

**Share this URL:** `https://abc123.ngrok-free.app`

---

## 👥 Demo Credentials

Tell users to login with:
- **Username:** `demo`
- **Password:** `demo123`

---

## ✅ What Works

Users can:
- ✅ View landing page
- ✅ Login as demo user
- ✅ Chat with AI assistant
- ✅ Log moods and activities
- ✅ View challenges and progress
- ✅ See insights and analytics
- ✅ Complete wellness activities

---

## 📊 Monitor Traffic

While ngrok runs, visit: `http://127.0.0.1:4040`

See:
- Real-time requests
- Response times
- Request/response details
- Traffic statistics

---

## ⚠️ Important Notes

1. **Free Plan Limits:**
   - URL changes each restart
   - 2-hour session timeout
   - "Visit Site" button for users (normal)

2. **Keep Running:**
   - Don't close terminals
   - Backend must stay running
   - ngrok must stay running

3. **New URL Each Time:**
   - URL changes when you restart ngrok
   - Share the new URL each time

---

## 🎯 Full Demo Flow

1. Start backend: `python backend/start_no_reload.py`
2. Start ngrok: `ngrok http 8000`
3. Copy the `https://xxx.ngrok-free.app` URL
4. Share URL with others
5. Tell them: username `demo`, password `demo123`
6. They click "Visit Site" (if prompted)
7. They login and use the app!

---

## 🐛 Troubleshooting

**"ngrok not found"**
- Add ngrok.exe to PATH or use full path: `C:\path\to\ngrok.exe http 8000`

**"Failed to start tunnel"**
- Run: `ngrok config add-authtoken YOUR_TOKEN`

**"Connection refused"**
- Make sure backend is running: `curl http://localhost:8000/health`

**CORS errors**
- Already configured! Should work out of the box.

---

## 🎉 You're Done!

Your MoodCapture app is now accessible worldwide! Share the ngrok URL and let others try it.

**Pro Tip:** Test the public URL yourself before sharing to make sure everything works!
