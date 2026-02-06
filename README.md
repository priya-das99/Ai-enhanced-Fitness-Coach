# 🧠 MoodCapture - AI-Enhanced Mood Tracking & Wellness Suggestions

> **Experimental Project:** Exploring OpenAI integration for personalized wellness recommendations

A Flask-based mood tracking application that uses OpenAI's GPT-4o-mini to provide intelligent wellness suggestions based on user mood and context.

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-0.28.1-orange.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [Demo](#-demo)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Cost Analysis](#-cost-analysis)
- [Project Structure](#-project-structure)
- [Experimentation Notes](#-experimentation-notes)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

- 🎭 **Mood Tracking** - Log emotional states with optional reasons
- 🤖 **AI-Powered Suggestions** - OpenAI GPT-4o-mini selects personalized wellness activities
- 🧠 **Smart Fallback System** - Context-aware rule-based suggestions when AI is unavailable
- ⏰ **Context Awareness** - Considers time of day, work hours, and recent suggestions
- 📹 **Video Resources** - Curated YouTube videos for each wellness activity
- 📊 **Historical Tracking** - View mood logs and patterns over time
- 💰 **Cost Tracking** - Built-in tools to monitor OpenAI API usage and costs

---

## 🎬 Demo

### User Flow

```
1. User selects mood (Happy, Horrible, Tired, etc.)
   ↓
2. If negative mood → Select reason (Work Stress, Sleep, etc.)
   ↓
3. System logs mood to database
   ↓
4. AI selects best wellness activity:
   - breathing
   - meditation
   - stretching
   - take_break
   - short_walk
   ↓
5. User receives personalized suggestion + video resources
```

### Example Response

```json
{
  "status": "success",
  "suggestion": {
    "text": "Work stress can be overwhelming. Try a 5-minute breathing exercise...",
    "category": "breathing",
    "source": "openai_llm"
  },
  "videos": [
    {
      "title": "5-Minute Stress Relief Meditation",
      "type": "Meditation",
      "url": "https://www.youtube.com/watch?v=..."
    }
  ]
}
```

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                        │
│  - Mood selection UI                                         │
│  - Reason selection (conditional)                            │
│  - Suggestion display with videos                            │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/JSON
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    Flask Backend (app.py)                    │
│  - POST /api/mood - Log mood & get suggestions               │
│  - GET /logs - View mood history                             │
│  - GET /api/logs - Get logs as JSON                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
┌──────────────┐ ┌──────────┐ ┌─────────────────┐
│ LLM Service  │ │ Database │ │ Config/Env      │
│ (OpenAI)     │ │ (SQLite) │ │ (.env)          │
└──────────────┘ └──────────┘ └─────────────────┘
```

### AI Suggestion Flow

```
User Request (negative mood)
    ↓
llm_service.select_suggestion_with_llm()
    ↓
    ├─→ Try OpenAI API (gpt-4o-mini)
    │   ├─→ Rate limiting check (1 call/second)
    │   ├─→ Context gathering (time, work hours)
    │   ├─→ Prompt construction
    │   ├─→ API call
    │   └─→ Response parsing & validation
    │       ├─→ Success: Return LLM suggestion ✅
    │       └─→ Fail: Continue to fallback
    │
    └─→ Smart Rule-Based Fallback
        ├─→ Filter by work hours
        ├─→ Filter by time of day
        ├─→ Avoid recent suggestions
        └─→ Return context-aware suggestion ✅
```

---

## 🚀 Installation

### Prerequisites

- Python 3.x
- pip
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/moodcapture.git
cd moodcapture

# 2. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# 5. Initialize database
python db.py

# 6. Run the application
python app.py
```

The application will be available at `http://localhost:5000`

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-...your-key-here...

# LLM Model (optional, defaults to gpt-4o-mini)
LLM_MODEL=gpt-4o-mini

# Enable/Disable LLM (optional, defaults to true)
ENABLE_LLM=true
```

### Important Notes

- ⚠️ **No whitespace** - Ensure no trailing spaces/newlines in API key
- ✅ **Key format** - Must start with `sk-` for OpenAI
- 💳 **Billing** - Ensure OpenAI account has credits/active billing

### Configuration Options

```python
# config.py
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip() or None
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini').strip()
ENABLE_LLM = os.getenv('ENABLE_LLM', 'true').lower() == 'true'
LLM_TIMEOUT = 10  # seconds
MAX_RETRIES = 2
```

---

## 📖 Usage

### Web Interface

1. **Open browser** → `http://localhost:5000`
2. **Select mood** → Click on mood button (Happy, Horrible, Tired, etc.)
3. **Select reason** (if negative mood) → Click reason button
4. **Submit** → Click "Submit Mood"
5. **View suggestion** → See AI-generated wellness suggestion + videos

### View Mood History

- Navigate to `http://localhost:5000/logs`
- See all logged moods in a table format

### API Usage

```bash
# Log a mood
curl -X POST http://localhost:5000/api/mood \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "web_user",
    "mood": "horrible",
    "reason": "work_stress"
  }'

# Get mood logs
curl http://localhost:5000/api/logs
```

---

## 📡 API Documentation

### POST /api/mood

Log user mood and get AI suggestions.

**Request:**
```json
{
  "user_id": "web_user",
  "mood": "horrible",
  "reason": "work_stress"
}
```

**Response (Negative Mood):**
```json
{
  "status": "success",
  "message": "Mood 'horrible' logged successfully",
  "suggestion": {
    "text": "Work stress can be overwhelming. Try a 5-minute breathing exercise...",
    "category": "breathing",
    "source": "openai_llm"
  },
  "videos": [
    {
      "title": "5-Minute Stress Relief Meditation",
      "type": "Meditation",
      "url": "https://www.youtube.com/watch?v=..."
    }
  ]
}
```

**Response (Positive Mood):**
```json
{
  "status": "success",
  "message": "Mood 'happy' logged successfully"
}
```

### GET /api/logs

Get mood logs as JSON.

**Response:**
```json
[
  {
    "id": 1,
    "user_id": "web_user",
    "mood": "horrible",
    "reason": "work_stress",
    "timestamp": "2026-02-05 14:52:16"
  }
]
```

---

## 🧪 Testing

### Quick Test

Test OpenAI integration with a single request:

```bash
python quick_test.py
```

### User Flow Simulation

Simulate a user clicking for a suggestion:

```bash
python demo_user_click.py
```

**Output:**
```
👤 USER ACTION: User 'Alice' clicks 'Get Suggestion' button
📝 User Input:
   - Mood: horrible
   - Reason: work_stress

🔄 Processing...
    🌐 Making OpenAI API call...
    ✓ API responded successfully
    📊 Tokens used: 99 (prompt: 97, completion: 2)

✅ RESPONSE TO USER:
   - Suggestion: breathing
   - Source: openai_llm
   - 💰 OpenAI API was used (costs money)
```

### Batch Testing

Track API usage across multiple tests:

```bash
python track_llm_usage.py 10  # Run 10 tests
```

### Detailed Metrics

Get comprehensive metrics with token tracking:

```bash
python test_llm_metrics_live.py
```

---

## 💰 Cost Analysis

### Current Implementation

**Per API Call:**
- Average tokens: ~98 tokens
- Prompt tokens: ~96 tokens
- Completion tokens: ~2 tokens
- **Cost per call: ~$0.000016**

### Pricing (gpt-4o-mini)

- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

### Projected Costs

| Users/Day | API Calls/Day | Cost/Day | Cost/Month | Cost/Year |
|-----------|---------------|----------|------------|-----------|
| 100       | 100           | $0.001   | $0.03      | $0.36     |
| 1,000     | 1,000         | $0.01    | $0.30      | $3.65     |
| 10,000    | 10,000        | $0.10    | $3.00      | $36.50    |
| 100,000   | 100,000       | $1.00    | $30.00     | $365.00   |

### Cost Optimization

**Current Approach:**
- ✅ Rate limiting (1 call/second)
- ✅ Smart fallback (free rule-based system)
- ✅ Short prompts (predefined categories)
- ✅ Low temperature (0.3) for consistency

**Recommendations:**
1. **Disable LLM for MVP** - Use free rule-based system
2. **Cache suggestions** - Reuse for similar requests
3. **Premium tier only** - Reserve AI for paying users
4. **Hybrid approach** - 90% rules, 10% AI

---

## 📁 Project Structure

```
moodcapture/
├── app.py                          # Flask application & API endpoints
├── llm_service.py                  # OpenAI integration & smart fallback
├── db.py                           # SQLite database operations
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (not in git)
├── mood.db                         # SQLite database (auto-created)
│
├── templates/
│   ├── index.html                  # Main mood tracking UI
│   └── logs.html                   # Mood history view
│
├── static/                         # Static assets (if any)
│
├── testing/
│   ├── quick_test.py               # Quick OpenAI test
│   ├── demo_user_click.py          # User flow simulation
│   ├── track_llm_usage.py          # Batch usage tracking
│   └── test_llm_metrics_live.py    # Detailed metrics
│
├── docs/
│   └── OPENAI_INTEGRATION_DOCS.md  # Detailed integration docs
│
└── README.md                       # This file
```

---

## 🔬 Experimentation Notes

### What We're Testing

1. **AI vs Rule-Based Suggestions**
   - Does AI provide better suggestions than rules?
   - Is the cost justified?
   - User satisfaction comparison

2. **Context Awareness**
   - Does time-of-day matter?
   - Work hours vs personal time
   - Recent suggestion avoidance

3. **Cost-Effectiveness**
   - Token usage optimization
   - Fallback trigger rate
   - ROI analysis

### Key Findings

✅ **What Works:**
- OpenAI integration is reliable with proper error handling
- Smart fallback ensures 100% uptime
- Context-aware suggestions feel more personalized
- Rate limiting prevents cost overruns

⚠️ **Challenges:**
- Current use case (selecting from 5 options) doesn't justify AI cost
- Rule-based system can achieve similar results for free
- Need more complex use case to justify LLM usage

💡 **Insights:**
- LLM is overkill for simple category selection
- Better use case: Generate unique, personalized suggestions
- Hybrid approach (rules + occasional AI) is most cost-effective

### Future Experiments

- [ ] Generate personalized suggestions instead of selecting categories
- [ ] A/B test AI vs rules with real users
- [ ] Implement caching for similar requests
- [ ] Try different models (GPT-4, Claude, Gemini)
- [ ] Add user feedback loop to improve suggestions

---

## 🛠️ Tech Stack

### Backend
- **Flask 3.x** - Web framework
- **Python 3.x** - Programming language
- **SQLite 3** - Database
- **OpenAI 0.28.1** - AI/ML (legacy SDK)
- **python-dotenv** - Environment management

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling
- **Vanilla JavaScript** - Interactivity
- **Fetch API** - AJAX requests

### Dependencies

```txt
flask          # Web framework
openai==0.28.1 # OpenAI SDK (legacy version)
python-dotenv  # Environment variable management
```

---

## 🐛 Troubleshooting

### Issue: API Key Not Loading

**Symptoms:**
- Logs show "No OpenAI API key found in environment"
- All requests fall back to rule-based suggestions

**Solution:**
1. Check `.env` file exists in project root
2. Verify `OPENAI_API_KEY` is set correctly (no whitespace)
3. Run diagnostic: `python quick_test.py`

### Issue: API Calls Failing

**Symptoms:**
- Error: "You exceeded your current quota"
- Error: "RateLimitError"

**Solution:**
1. Check OpenAI account billing: https://platform.openai.com/account/billing
2. Add credits or upgrade plan
3. Verify API key is valid

### Issue: Rate Limiting

**Symptoms:**
- Logs show "Rate limiting: skipping OpenAI call"
- Some users get rule-based suggestions

**Solution:**
- This is expected behavior (1 call per second limit)
- Adjust `MIN_CALL_INTERVAL` in `llm_service.py` if needed
- Consider caching suggestions for similar requests

---

## 🤝 Contributing

This is an experimental project, but contributions are welcome!

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution

- 🎨 UI/UX improvements
- 🧪 Additional testing tools
- 📊 Analytics and metrics
- 🌐 Multi-language support
- 🔒 Security enhancements
- 📱 Mobile responsiveness

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- OpenAI for GPT-4o-mini API
- Flask community for excellent documentation
- YouTube creators for wellness content

---

## 📞 Contact

For questions or feedback about this experiment:

- **GitHub Issues:** [Create an issue](https://github.com/yourusername/moodcapture/issues)
- **Email:** your.email@example.com

---

## 📊 Project Status

🔬 **Status:** Experimental / Proof of Concept

**Last Updated:** February 6, 2026

**Next Steps:**
- [ ] A/B testing with real users
- [ ] Cost optimization experiments
- [ ] Personalized suggestion generation
- [ ] User feedback collection
- [ ] Production deployment considerations

---

Made with ❤️ and 🤖 by [Your Name]
