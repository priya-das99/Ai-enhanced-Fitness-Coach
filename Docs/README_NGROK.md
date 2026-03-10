# 🌐 Share MoodCapture Demo with ngrok

## 🎯 Goal
Make your local MoodCapture app accessible to anyone on the internet for demos and presentations.

---

## ⚡ Quick Start (3 Steps)

### 1️⃣ Install ngrok
- Download: https://ngrok.com/download
- Extract `ngrok.exe` anywhere
- Sign up (free): https://dashboard.ngrok.com/signup
- Get auth token: https://dashboard.ngrok.com/get-started/your-authtoken
- Run: `ngrok config add-authtoken YOUR_TOKEN`

### 2️⃣ Start Backend
```powershell
python backend/start_no_reload.py
```
Wait for: `Uvicorn running on http://127.0.0.1:8000`

### 3️⃣ Start ngrok
```powershell
ngrok http 8000
```

Copy the URL shown (e.g., `https://abc123.ngrok-free.app`)

---

## 📤 Share with Others

**Send them:**
- URL: `https://abc123.ngrok-free.app`
- Username: `demo`
- Password: `demo123`

**They can:**
- View the app
- Login and use all features
- Chat with AI assistant
- Log moods and activities
- View challenges and insights

---

## 📊 Monitor Activity

While ngrok runs, visit: http://127.0.0.1:4040

See all requests, responses, and traffic in real-time!

---

## ⚠️ Important

- ✅ Free plan works great for demos
- ⚠️ URL changes each time you restart ngrok
- ⚠️ Keep both terminals running
- ⚠️ Users may see "Visit Site" button (normal, just click it)

---

## 📚 Full Documentation

- **Quick Guide:** `QUICK_START_NGROK.md`
- **Detailed Setup:** `NGROK_SETUP_GUIDE.md`
- **Check Readiness:** `python check_demo_ready.py`

---

## 🎉 That's It!

Your local MoodCapture is now accessible worldwide! Perfect for:
- 🎤 Presentations
- 👥 User testing
- 🎓 Demos
- 🤝 Sharing with team

**Pro Tip:** Always test the public URL yourself before sharing!
