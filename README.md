# AI-Enhanced Fitness Coach & Mood Capture

An intelligent fitness coaching application that combines mood tracking, personalized activity suggestions, and AI-powered chat assistance to provide a comprehensive wellness experience.

## Features

- **Mood Tracking**: Capture and analyze daily mood patterns
- **AI Chat Assistant**: Intelligent conversation engine with context-aware responses
- **Activity Recommendations**: Personalized fitness and wellness suggestions
- **Challenge System**: Gamified fitness challenges and progress tracking
- **Analytics Dashboard**: Comprehensive insights into user behavior and progress
- **Multi-Modal Interface**: Web-based frontend with responsive design

## Project Structure

```
├── backend/                 # FastAPI backend application
│   ├── app/                # Main application code
│   │   ├── api/           # API endpoints and routing
│   │   ├── core/          # Core functionality (database, security)
│   │   ├── models/        # Data models
│   │   ├── repositories/  # Data access layer
│   │   └── services/      # Business logic
│   ├── chat_assistant/    # AI chat engine and workflows
│   ├── migrations/        # Database migrations
│   └── tests/            # Test suite
├── frontend/              # Web frontend
├── Docs/                 # Comprehensive documentation
└── mood_capture.db       # SQLite database
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js (for frontend development)
- SQLite

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
python init_db.py
```

6. Start the development server:
```bash
python start_no_reload.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Open `index.html` in your browser or serve with a local server

## API Documentation

Once the backend is running, visit:
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Key Components

### Chat Assistant
- Context-aware conversation engine
- Multiple workflow types (mood, activity, general)
- Intelligent suggestion system
- Safety and validation layers

### Analytics System
- User behavior tracking
- Insight generation
- Pattern detection
- Personalized recommendations

### Challenge System
- Dynamic challenge creation
- Progress tracking
- Gamification elements


## Documentation

Comprehensive documentation is available in the `Docs/` directory:


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request


