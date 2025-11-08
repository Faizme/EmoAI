from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import pytz

db = SQLAlchemy()

IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    return datetime.now(IST)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=get_ist_now)
    
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    journals = db.relationship('Journal', backref='user', lazy=True, cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='user', lazy=True, cascade='all, delete-orphan')

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    goal = db.Column(db.Text, nullable=False)
    reminder_enabled = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=get_ist_now)

class Journal(db.Model):
    __tablename__ = 'journals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood = db.Column(db.String(50), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    goal_progress = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<Journal {self.id} - {self.mood} on {self.timestamp}>'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<ChatMessage {self.id} - {self.role}>'

class HabitProgress(db.Model):
    __tablename__ = 'habit_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    progress_note = db.Column(db.Text, nullable=True)
    mood = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<HabitProgress {self.id} - {self.date}>'

class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    time = db.Column(db.String(10), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<Reminder {self.id} - {self.message[:20]}...>'

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_days = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_ist_now)
    
    activities = db.relationship('Activity', backref='goal', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Goal {self.id} - {self.title}>'

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<Activity {self.id} - {self.activity_type}>'

class MotivationMessage(db.Model):
    __tablename__ = 'motivation_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<MotivationMessage {self.id}>'

class SleepLog(db.Model):
    __tablename__ = 'sleep_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    bedtime = db.Column(db.String(10), nullable=True)
    wake_time = db.Column(db.String(10), nullable=True)
    hours_slept = db.Column(db.Float, nullable=True)
    quality_rating = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<SleepLog {self.id} - {self.date}>'

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.String(10), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    is_confirmed = db.Column(db.Boolean, default=False)
    is_in_google_calendar = db.Column(db.Boolean, default=False)
    google_calendar_id = db.Column(db.String(200), nullable=True)
    created_from_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<Event {self.id} - {self.title}>'

class UserSentiment(db.Model):
    __tablename__ = 'user_sentiments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    sentiment = db.Column(db.String(50), nullable=False)
    intensity = db.Column(db.Float, default=0.5)
    timestamp = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<UserSentiment {self.id} - {self.sentiment}>'

class GoogleCalendarToken(db.Model):
    __tablename__ = 'google_calendar_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    token_uri = db.Column(db.String(200), nullable=True)
    client_id = db.Column(db.String(200), nullable=True)
    client_secret = db.Column(db.String(200), nullable=True)
    scopes = db.Column(db.Text, nullable=True)
    expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=get_ist_now)
    updated_at = db.Column(db.DateTime, default=get_ist_now, onupdate=get_ist_now)
    
    def __repr__(self):
        return f'<GoogleCalendarToken {self.id} - User {self.user_id}>'
