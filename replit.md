# VIBE JOURNAL AI - Full-Stack Emotional Wellness App

## Overview

Vibe Journal AI is a comprehensive full-stack web application that helps users reflect on their emotions daily through conversational AI. The app stores journal entries automatically, tracks personal goals, and provides gentle reminders for self-improvement. Built with Flask for the backend, SQLite for data persistence, and vanilla JavaScript for the frontend, it uses Google's Generative AI (Gemini 2.0) to power an empathetic conversational companion.

## Recent Changes (November 2025)

- **Complete rebuild** from simple chatbot to full-featured journaling app
- Implemented authentication system with Flask-Login and bcrypt
- Created database models for Users, UserProfiles, Journals, and ChatMessages
- Built complete user journey: Signup → About → Onboarding → Chatbot → Journal
- Applied premium dark mode neo-noir UI design with glassmorphism
- Added personalized AI responses based on user goals
- Implemented journal storage with mood tracking and goal progress
- Fixed critical session storage issue by moving chat history to database
- **Added Daily Reminders & Habit Progress feature** (November 8, 2025):
  - Daily reminder popup with personalized messages
  - Habit progress tracking with notes
  - 7-day streak visualization on dashboard
  - Reminder settings modal with toggle and time picker
  - Auto-cleanup of progress older than 30 days
  - Bell icon with animated notification

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack**: Vanilla JavaScript, HTML5, CSS3

The frontend implements a multi-page application with premium dark mode styling:

**Key Design Decisions**:
- **Neo-Noir Dark Theme**: Deep purple to teal gradients with glassmorphism effects
- **Page Transitions**: Smooth fade and slide animations between pages
- **No Framework Approach**: Lightweight vanilla JS for focused functionality
- **Responsive Design**: Mobile-first approach with fluid layouts

### Backend Architecture

**Framework**: Flask 3.0+ with Flask-Login, Flask-SQLAlchemy, Flask-Bcrypt

The backend follows an MVC pattern with route-based organization:

**Key Design Decisions**:
- **Database-backed Chat History**: Chat messages stored in SQLite to avoid session cookie limits
- **Session-based Authentication**: Flask-Login for secure user session management
- **Password Security**: Bcrypt hashing for all user passwords
- **Per-user Data Isolation**: All data scoped to authenticated user

### Database Architecture

**Technology**: SQLite with SQLAlchemy ORM

**Tables**:
1. **Users**: Email, password hash, timestamps
2. **UserProfile**: Name, age, goal, reminder_enabled, reminder_time (1:1 with User)
3. **Journal**: Mood, summary, goal progress, timestamps (many:1 with User)
4. **ChatMessage**: Session ID, role, content, timestamps (many:1 with User)
5. **HabitProgress**: Date, progress note, mood, timestamps (many:1 with User)

**Key Design Decisions**:
- **Chat History in Database**: Prevents session cookie overflow for long conversations
- **Session-based Chat Isolation**: Each chat session gets unique ID
- **Cascading Deletes**: User deletion removes all associated data
- **SQLite for Simplicity**: Perfect for MVP, easily upgradable to PostgreSQL

### AI/ML Architecture

**Provider**: Google Generative AI (Gemini 2.0 Flash)

**Dual-Model Approach**:
1. **Conversational Model (VILUN)**: Warm, empathetic companion with context awareness
2. **Summarization Model**: Transforms conversations into first-person journal entries

**Key Design Decisions**:
- **User Context Integration**: AI receives user's name, age, and goals for personalization
- **Database-backed History**: Full conversation context without size limits
- **Stateless AI Calls**: Each request provides complete history for continuity

### Authentication & Security

**Implementation**: Flask-Login + Bcrypt

**Security Measures**:
- Bcrypt password hashing (cost factor 12+)
- Session cookie encryption with secret key
- CSRF protection via Flask defaults
- XSS prevention through HTML escaping
- User data isolation at database level

## User Journey

### 1. Landing Page (Login/Signup)
- Dark hero UI with glassmorphism card
- Email + password authentication
- Smooth animations and floating particle effects

### 2. About Page
- Storytelling about app benefits
- Parallax scrolling effects
- Smooth transitions to onboarding

### 3. Onboarding (First-time users only)
- Collects name, age (optional), and personal goal
- Beautiful gradient forms with glassmorphism
- Skipped for returning users

### 4. Chatbot Interface
- Full-screen chat with VILUN AI
- Personalized greetings using user's name
- Typing indicators and smooth animations
- Mood tracking and goal progress questions

### 5. Journal Summary
- AI-generated summary of conversation
- Mood selection with emoji indicators
- Goal progress notes (optional)
- Save to journal database

### 6. Journal View
- Historical entries in beautiful cards
- Shows date, mood, summary, and goal progress
- Sorted by most recent first

## External Dependencies

### Third-party Services

**Google Generative AI (Gemini 2.0 API)**
- **Purpose**: Powers conversational AI and summarization
- **Integration Point**: `attached_assets/ai_core_1762554001118.py`
- **Configuration**: Requires `GOOGLE_API_KEY` environment variable
- **Models Used**: `gemini-2.0-flash` for both chat and summarization

### Python Packages

**Flask** (>=3.0.0)
- Web framework for routing, templating, and request handling

**Flask-Login** (>=0.6.3)
- User session management and authentication

**Flask-SQLAlchemy** (>=3.1.1)
- ORM for database operations

**Flask-Bcrypt** (>=1.0.1)
- Password hashing and verification

**google-generativeai** (>=0.3.0)
- Official Google SDK for Generative AI

### Environment Variables

**Required**:
- `GOOGLE_API_KEY`: Authentication for Google Generative AI services

**Optional**:
- `SECRET_KEY`: Flask session encryption key (auto-generated if not provided)

### Frontend Dependencies

No external frontend libraries or CDNs required - uses native browser APIs exclusively.

## Project Structure

```
├── app.py                      # Main Flask application
├── models.py                   # SQLAlchemy database models
├── templates/                  # HTML templates
│   ├── base.html              # Base template with CSS/JS includes
│   ├── login.html             # Login page
│   ├── signup.html            # Signup page
│   ├── about.html             # About page
│   ├── onboarding.html        # Onboarding form
│   ├── chatbot.html           # Main chat interface with reminders
│   ├── dashboard.html         # Habit streak & progress dashboard
│   └── journal.html           # Journal history view
├── static/
│   ├── css/
│   │   ├── main.css           # Global dark theme styles
│   │   └── chatbot.css        # Chat-specific styles
│   └── js/
│       ├── main.js            # Global JavaScript utilities
│       └── chatbot.js         # Chat interface logic
├── attached_assets/
│   └── ai_core_1762554001118.py  # Gemini AI integration
└── instance/
    └── vibe_journal.db        # SQLite database (auto-created)
```

## Features Implemented

✅ **User Authentication**: Secure signup/login with password hashing  
✅ **User Onboarding**: Collect name, age, and personal improvement goals  
✅ **AI Chat Companion**: Empathetic VILUN chatbot with user personalization  
✅ **Database Chat Storage**: Unlimited conversation length  
✅ **Journal Summarization**: AI-powered conversation summaries  
✅ **Mood Tracking**: Emoji-based mood selection  
✅ **Goal Progress Tracking**: Optional notes on daily progress  
✅ **Journal History**: View all past entries with beautiful cards  
✅ **Daily Habit Reminders**: Personalized popup on login with Yes/Not today buttons  
✅ **Habit Progress Tracking**: Save daily progress notes with timestamps  
✅ **7-Day Streak Dashboard**: Visual tracker with supportive messages  
✅ **Reminder Settings**: Toggle and time picker with bell icon in navbar  
✅ **Auto Data Cleanup**: Automatically deletes progress older than 30 days  
✅ **Premium Dark UI**: Neo-noir theme with glassmorphism  
✅ **Responsive Design**: Works on desktop and mobile  
✅ **Session Management**: Isolated conversations per user

## Security Notes

- All passwords are hashed with bcrypt
- Session cookies are encrypted
- User data is isolated per account
- XSS protection via template escaping
- No sensitive data in client-side storage
- Chat history stored server-side only
- Habit progress data auto-deleted after 30 days

## Database Migration Notes

**Important**: When updating to the version with Daily Reminders & Habit Progress:
- The database schema has been updated with new fields and tables
- For development: Delete `instance/vibe_journal.db` and restart the app to recreate with new schema
- For production: Use proper database migration tools (Alembic/Flask-Migrate) to preserve existing data
- New schema adds: `reminder_time` column to UserProfile and `HabitProgress` table

## Future Enhancements

- Email verification for signup
- Password reset functionality
- Daily reminder notifications (UI implementation)
- Export journal entries as PDF
- Mood analytics dashboard
- Goal progress visualization
- Multi-language support
- Dark/light theme toggle
- Voice input for chat
