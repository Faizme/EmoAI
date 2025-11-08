# EMOAI - Full-Stack Emotional Wellness App

## Overview

EmoAI is a comprehensive full-stack web application designed to help users improve their lives through AI-powered support. It helps users quit bad habits, build better ones, and achieve personal goals through emotionally intelligent conversations. The app provides daily check-ins, personalized advice, habit tracking with streaks, voice interactions, and automatic journaling. It leverages Google's Generative AI (Gemini 2.0) to power a feeling-first, goal-oriented companion that understands emotional subtext while offering practical guidance.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions

The application features an elegant, sophisticated Wix Studio-inspired aesthetic with a warm color palette. Key design elements include:

-   **Color Scheme**: Warm browns, teals, beige backgrounds (RGB(249,244,233)), sage green accents (RGB(107, 169, 159)), peach highlights (RGB(232, 181, 166)), and lavender touches (RGB(201, 181, 227)).
-   **Typography**: Playfair Display serif for headings and Inter for body text.
-   **Visuals**: High-quality 3D stock illustrations integrated across hero sections, soft gradients, subtle shadows, and floating decorative shapes.
-   **Layout**: Split-screen authentication pages and a responsive design optimized for all screen sizes.

### Technical Implementations

-   **Frontend**: Built with Vanilla JavaScript, HTML5, and CSS3, focusing on a lightweight, no-framework approach for focused functionality and accessibility.
-   **Backend**: Flask 3.0+ framework utilizing Flask-Login for secure authentication, Flask-SQLAlchemy for ORM, and Flask-Bcrypt for password hashing. It follows an MVC pattern with route-based organization.
-   **Database**: SQLite with SQLAlchemy ORM for data persistence.
-   **AI/ML**: Google Generative AI (Gemini 2.0 Flash) is used as a dual-model approach for conversational AI and summarization. The AI is designed to be deeply emotionally intelligent, understanding subtext and responding with nuanced, feeling-first interactions.
-   **Authentication & Security**: Implemented using Flask-Login and Bcrypt for password hashing, session cookie encryption, CSRF protection, XSS prevention, and user data isolation.

### Feature Specifications

-   **User Management**: Secure signup/login, onboarding for collecting user goals.
-   **AI Chat**: Personalized, empathetic conversational AI companion for habit-quitting, life improvement, and emotional support. Includes voice-to-text input and text-to-speech responses using Web Speech API.
-   **Goals & Activities**: 
    - Separate interfaces for "Quit Bad Habits" vs "Build New Skills"
    - Different activity types for each goal category
    - Visual progress tracking with colored progress bars
    - Habits activities: Deep Breathing, Take a Walk, Journal Entry
    - Achievement activities: Practice Session, Complete Lesson, Do Exercise
-   **Positive Reinforcement**: Swiggy-style motivational toast notifications that appear after completing activities, with context-aware encouraging messages
-   **Sleep Tracker**: Full sleep monitoring interface with bedtime/wake time logging, quality ratings, sleep insights dashboard, 14-day history, and sleep improvement tips
-   **Journaling**: AI-generated conversation summaries, mood tracking, goal progress notes, and historical journal entry viewing.
-   **Reminders & Habits**: Daily personalized reminder popups, custom reminder creation and management, habit progress tracking, and a 7-day streak visualization.
-   **Data Management**: Chat history and habit progress are stored in the database, with automatic cleanup of habit progress older than 30 days.

### System Design Choices

-   **Database-backed Chat History**: Stores chat messages in SQLite to overcome session cookie limitations.
-   **Per-user Data Isolation**: All user data is securely scoped to the authenticated user.
-   **Stateless AI Calls**: Each AI request includes the complete conversation history for continuity, maintaining a session-like experience without stateful AI processing.

## External Dependencies

### Third-party Services

-   **Google Generative AI (Gemini 2.0 API)**: Powers the conversational AI and summarization features. Configured via the `GOOGLE_API_KEY` environment variable.

### Python Packages

-   **Flask** (>=3.0.0): Web framework.
-   **Flask-Login** (>=0.6.3): User session management and authentication.
-   **Flask-SQLAlchemy** (>=3.1.1): ORM for database operations.
-   **Flask-Bcrypt** (>=1.0.1): Password hashing and verification.
-   **google-generativeai** (>=0.3.0): Official Google SDK for Generative AI.

### Environment Variables

-   `GOOGLE_API_KEY`: Required for Google Generative AI services.
-   `SECRET_KEY`: Optional, used for Flask session encryption.