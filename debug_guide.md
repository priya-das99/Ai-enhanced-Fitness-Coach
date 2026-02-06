# How to See if Response is LLM or Fallback

## Method 1: Visual Indicator on Webpage ✨
- **LLM-Enhanced**: Shows "✨ AI-Enhanced" badge below suggestion
- **Fallback**: Shows "🔧 Rule-Based" badge below suggestion

## Method 2: Browser Developer Console 🔍
1. Open browser (Chrome/Firefox/Edge)
2. Press `F12` or right-click → "Inspect"
3. Go to "Console" tab
4. Submit a negative mood
5. Look for logs like:
   ```
   🤖 Suggestion Details: {source: "llm_enhanced", category: "breathing", text: "Work stress..."}
   ✨ AI-Enhanced Suggestion: Selected "breathing" based on your context
   ```

## Method 3: Flask Server Logs 📋
Check the terminal where you ran `python app.py`:
```
INFO:app:✨ LLM-Enhanced suggestion: category='breathing', user='web_user', mood='not good'
INFO:app:🔧 Rule-based fallback suggestion: user='web_user', mood='tired'
```

## Method 4: Debug Mode Toggle 🐛
In browser console, type:
```javascript
toggleDebugMode()  // Enable debug messages
```
Then submit moods to see debug info in the message area.

## Method 5: API Response Inspection 🔧
Use browser Network tab:
1. Open Developer Tools → Network tab
2. Submit a mood
3. Click on the `/api/mood` request
4. Check Response:
   ```json
   {
     "suggestion": {
       "text": "Work stress is common...",
       "category": "breathing", 
       "source": "llm_enhanced"
     }
   }
   ```

## Method 6: Test Script 🧪
Run the test script:
```bash
python test_suggestion_response.py
```

## Quick Test Scenarios

### To Force LLM Response:
- Mood: "not good" 
- Reason: "work_stress"
- Expected: ✨ AI-Enhanced with smart category selection

### To Force Fallback:
- Disable LLM in `.env`: `ENABLE_LLM=false`
- Any negative mood
- Expected: 🔧 Rule-Based

### Current Status:
- LLM is **enabled** and working with Gemini
- Smart selection is active
- Fallback system is ready if LLM fails