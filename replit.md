# VILUN - AI Companion & Journal

## Overview

VILUN is a web-based conversational AI companion that provides emotional support and journaling capabilities. The application combines real-time chat functionality with the ability to summarize conversations into journal entries. Built with Flask for the backend and vanilla JavaScript for the frontend, it uses Google's Generative AI (Gemini) to power two distinct AI personalities: a friendly companion for conversations and a summarizer for journal generation.

## Recent Changes (November 2025)

- Implemented complete Flask backend with REST API endpoints
- Created responsive chat interface with purple gradient design
- Added per-session storage for user privacy (Flask sessions)
- Integrated Google Gemini AI for conversational responses and journal summarization
- Configured workflow for automatic server restart on port 5000

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack**: Vanilla JavaScript, HTML5, CSS3

The frontend implements a single-page application (SPA) pattern without a framework, keeping the codebase lightweight and simple. The chat interface is built with standard DOM manipulation and fetch API for asynchronous communication.

**Key Design Decisions**:
- **No Framework Approach**: Chosen for simplicity and minimal dependencies, suitable for a focused chat interface
- **Session-based State**: Chat history is maintained server-side in Flask sessions rather than client-side storage, ensuring state persistence across page refreshes
- **Real-time UI Feedback**: Implements thinking indicators and message streaming to improve perceived responsiveness

### Backend Architecture

**Framework**: Flask 3.0.0+

The backend follows a simple REST API pattern with session management for conversation state.

**Key Design Decisions**:
- **Session-based Storage**: Chat history stored in Flask sessions (encrypted cookies) rather than a database
  - **Rationale**: Simplifies deployment and eliminates database dependency for MVP
  - **Trade-offs**: Limited scalability, no persistence across server restarts, storage limitations
  - **Alternative Considered**: Database storage would provide better persistence and scalability but adds complexity
- **Stateful Conversation Management**: Each user session maintains its own chat history array
- **Modular AI Core**: AI functionality separated into `attached_assets/ai_core_1762554001118.py` for clean separation of concerns

### AI/ML Architecture

**Provider**: Google Generative AI (Gemini 1.5 Flash)

**Dual-Model Approach**:
1. **Conversational Model (VILUN)**: Configured with empathetic, friend-like personality through system instructions
2. **Summarization Model**: Transforms conversations into first-person journal entries

**Key Design Decisions**:
- **Two Separate Model Instances**: Uses distinct system instructions for different behavioral contexts
  - **Rationale**: Separates conversational tone from summarization logic, allowing specialized prompts
  - **Pros**: Clear separation of concerns, optimized prompts for each task
  - **Cons**: Doubled API calls for summary feature
- **Stateless AI Integration**: Each request provides full chat history to maintain context
- **Environment-based Configuration**: API keys managed through environment variables for security

### Authentication & Security

**Current Implementation**: No user authentication system

**Security Measures**:
- Secret key for session encryption (environment variable or auto-generated)
- Session data stored in encrypted cookies
- API key protected via environment variables

**Note**: The current architecture assumes single-user or trusted environment usage. Multi-user deployment would require implementing user authentication and associating chat histories with user accounts.

## External Dependencies

### Third-party Services

**Google Generative AI (Gemini API)**
- **Purpose**: Powers conversational AI and summarization features
- **Integration Point**: `attached_assets/ai_core_1762554001118.py`
- **Configuration**: Requires `GOOGLE_API_KEY` environment variable
- **Models Used**: `gemini-1.5-flash` for both chat and summarization

### Python Packages

**Flask** (>=3.0.0)
- Web framework for routing, templating, and session management
- Provides the HTTP server and request handling

**google-generativeai** (>=0.3.0)
- Official Google SDK for Generative AI
- Handles API communication with Gemini models

### Environment Variables

**Required**:
- `GOOGLE_API_KEY`: Authentication for Google Generative AI services

**Optional**:
- `SECRET_KEY`: Flask session encryption key (auto-generated if not provided)

### Frontend Dependencies

No external frontend libraries or CDNs required - uses native browser APIs exclusively.