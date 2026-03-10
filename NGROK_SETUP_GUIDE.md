# 🌐 ngrok Setup Guide for MoodCapture Demo

## What is ngrok?
ngrok creates a secure tunnel from a public URL to your local server, allowing anyone to access your local MoodCapture app via the internet.

---

## 📥 Step 1: Install ngrok

### Option A: Download from Website (Recommended)
1. Go to https://ngrok.com/download
2. Download ngrok for Windows
3. Extract the `ngrok.exe` file to a folder (e.g., `C:\ngrok\`)
4. Add to PATH or use full path

### Option B: Using Chocolatey (if installed)
```powershell
choco install ngrok
```

### Option C: Using Scoop (if installed)
```powershell
scoop install ngrok
```

---

## 🔑 Step 2: Sign Up & Get Auth Token

1. Create free account at https://dashboard.ngrok.com/signup
2. Get your auth token from https://dashboard.ngrok.com/get-started/your-authtoken
3. Run this command (replace YOUR_TOKEN):
```powershell
ngrok config add-authtoken YOUR_TOKEN
```

---

## 🚀 Step 3: Start Your MoodCapture Server

Open **Terminal 1** and start the backend:
```powershell
cd E:\Vantage_Assignment\MoodCapture
python backend/start_no_reload.py
```

Your server should be running on `http://localhost:8000`

---

## 🌍 Step 4: Start ngrok Tunnel

Open **Terminal 2** and run:
```powershell
ngrok http 8000
```

You'll see output like:
```
ngrok                                                                           
                                                                                
Session Status                online                                            
Account                       your-email@example.com (Plan: Free)              
Version                       3.x.x                                             
Region                        United States (us)                                
Latency                       -                                                 
Web Interface                 http://127.0.0.1:4040                            
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90       
                              0       0       0.00    0.00    0.00    0.00      
```

---

## 🎯 Step 5: Access Your App

### Your Public URL
Copy the `Forwarding` URL (e.g., `https://abc123.ngrok-free.app`)

### Share with Others
Send them: `https://abc123.ngrok-free.app`

They can:
- ✅ View the landing page
- ✅ Login as demo user (username: `demo`, password: `demo123`)
- ✅ Use all features (chat, mood logging, challenges, etc.)

---

## 🔧 Step 6: Update CORS Settings (Important!)

Your FastAPI backend needs to allow the ngrok domain. Update `backend/app/main.py`:

```python
# Add ngrok domain to allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://*.ngrok-free.app",  # Add this line
        "*"  # Or use this for demo (less secure)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📱 ngrok Web Interface

While ngrok is running, visit `http://127.0.0.1:4040` to see:
- 📊 Real-time request logs
- 🔍 Request/response inspection
- 📈 Traffic statistics
- 🐛 Debugging information

---

## ⚡ Quick Start Commands

### Start Everything (2 Terminals)

**Terminal 1 - Backend:**
```powershell
cd E:\Vantage_Assignment\MoodCapture
python backend/start_no_reload.py
```

**Terminal 2 - ngrok:**
```powershell
ngrok http 8000
```

---

## 🎨 Custom Subdomain (Paid Plans)

With ngrok paid plan, you can use custom subdomains:
```powershell
ngrok http 8000 --subdomain=moodcapture-demo
```

This gives you: `https://moodcapture-demo.ngrok-free.app`

---

## 🔒 Security Tips

1. **Free Plan Limitations:**
   - URL changes every time you restart ngrok
   - Session timeout after 2 hours
   - Limited connections

2. **For Demo:**
   - ✅ Perfect for short demos/presentations
   - ✅ Share with specific people
   - ✅ Monitor via ngrok dashboard

3. **Don't Use For:**
   - ❌ Production deployments
   - ❌ Storing sensitive data
   - ❌ Long-term hosting

---

## 🐛 Troubleshooting

### Issue: "ngrok not found"
**Solution:** Add ngrok to PATH or use full path:
```powershell
C:\ngrok\ngrok.exe http 8000
```

### Issue: "Failed to start tunnel"
**Solution:** Make sure you added auth token:
```powershell
ngrok config add-authtoken YOUR_TOKEN
```

### Issue: "Connection refused"
**Solution:** Make sure backend is running on port 8000:
```powershell
# Check if server is running
curl http://localhost:8000/health
```

### Issue: CORS errors in browser
**Solution:** Update CORS settings in `backend/app/main.py` (see Step 6)

### Issue: ngrok URL shows "Visit Site" button
**Solution:** This is normal for free plan. Users just click "Visit Site" to continue.

---

## 📊 Alternative: ngrok with Static Files

If you want to serve frontend separately:

**Terminal 1 - Backend:**
```powershell
python backend/start_no_reload.py
```

**Terminal 2 - Frontend (if using separate server):**
```powershell
python -m http.server 3000
```

**Terminal 3 - ngrok for Backend:**
```powershell
ngrok http 8000
```

**Terminal 4 - ngrok for Frontend:**
```powershell
ngrok http 3000
```

---

## 🎯 Demo Checklist

Before sharing your ngrok URL:

- [ ] Backend server is running (`http://localhost:8000`)
- [ ] ngrok tunnel is active
- [ ] CORS is configured for ngrok domain
- [ ] Demo user exists (username: `demo`, password: `demo123`)
- [ ] Database has sample data
- [ ] Test the public URL yourself first
- [ ] Share the ngrok URL with others

---

## 🌟 Pro Tips

1. **Keep ngrok running** - Don't close the terminal
2. **Monitor requests** - Use ngrok web interface at `http://127.0.0.1:4040`
3. **Test first** - Always test the public URL before sharing
4. **Share credentials** - Tell users: username `demo`, password `demo123`
5. **Restart if needed** - If URL changes, share the new one

---

## 📞 Support

- ngrok Docs: https://ngrok.com/docs
- ngrok Dashboard: https://dashboard.ngrok.com
- MoodCapture Issues: https://github.com/priya-das99/Ai-enhanced-Fitness-Coach/issues

---

## ✅ You're Ready!

Once ngrok is running, share your URL and let others experience MoodCapture! 🎉
