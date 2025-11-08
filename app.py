from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, UserProfile, Journal, ChatMessage, HabitProgress, Reminder, Goal, Activity, MotivationMessage, SleepLog, Event, UserSentiment, GoogleCalendarToken
import os
import sys
import secrets
import random
from datetime import datetime, date, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), 'attached_assets'))
from ai_core_1762554001118 import get_ai_chat_response, summarize_chat_as_journal, extract_event_from_message, analyze_sentiment

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vibe_journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.profile:
            return redirect(url_for('chatbot'))
        else:
            return redirect(url_for('onboarding'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(email=email, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('about'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    if current_user.profile:
        return redirect(url_for('chatbot'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        goal = request.form.get('goal')
        
        if not name or not goal:
            flash('Name and goal are required', 'error')
            return redirect(url_for('onboarding'))
        
        profile = UserProfile(
            user_id=current_user.id,
            name=name,
            age=int(age) if age else None,
            goal=goal
        )
        db.session.add(profile)
        db.session.commit()
        
        return redirect(url_for('chatbot'))
    
    return render_template('onboarding.html')

@app.route('/chatbot')
@login_required
def chatbot():
    if not current_user.profile:
        return redirect(url_for('onboarding'))
    return render_template('chatbot.html', user_name=current_user.profile.name)

def get_session_id():
    if 'chat_session_id' not in session:
        session['chat_session_id'] = secrets.token_hex(16)
    return session['chat_session_id']

def get_chat_history_from_db():
    session_id = get_session_id()
    messages = ChatMessage.query.filter_by(
        user_id=current_user.id,
        session_id=session_id
    ).order_by(ChatMessage.timestamp).all()
    
    history = []
    for msg in messages:
        history.append({
            'role': msg.role,
            'parts': [msg.content]
        })
    return history

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    user_message = request.json.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    session_id = get_session_id()
    
    user_chat = ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role='user',
        content=user_message
    )
    db.session.add(user_chat)
    db.session.commit()
    
    try:
        detected_sentiment = analyze_sentiment(user_message)
        
        sentiment_record = UserSentiment(
            user_id=current_user.id,
            session_id=session_id,
            sentiment=detected_sentiment['sentiment'],
            intensity=detected_sentiment['intensity']
        )
        db.session.add(sentiment_record)
        
        current_datetime = datetime.now()
        detected_event = extract_event_from_message(user_message, current_datetime)
        
        event_data = None
        if detected_event:
            try:
                event_date = datetime.strptime(detected_event['date'], '%Y-%m-%d').date()
                event_time_str = detected_event.get('time')
                
                is_future_event = False
                if event_date > date.today():
                    is_future_event = True
                elif event_date == date.today() and event_time_str:
                    event_datetime = datetime.strptime(f"{detected_event['date']} {event_time_str}", '%Y-%m-%d %H:%M')
                    is_future_event = event_datetime > current_datetime
                
                if not is_future_event:
                    print(f"Rejected past event: {event_date} {event_time_str}")
                elif not detected_event.get('title'):
                    print(f"Rejected event without title")
                else:
                    new_event = Event(
                        user_id=current_user.id,
                        title=detected_event['title'],
                        event_date=event_date,
                        event_time=detected_event.get('time'),
                        location=detected_event.get('location'),
                        created_from_message=user_message,
                        is_confirmed=False
                    )
                    db.session.add(new_event)
                    db.session.flush()
                    
                    event_data = {
                        'id': new_event.id,
                        'title': new_event.title,
                        'date': new_event.event_date.isoformat(),
                        'time': new_event.event_time,
                        'location': new_event.location
                    }
            except Exception as event_error:
                print(f"Error creating event: {event_error}")
        
        chat_history = get_chat_history_from_db()
        
        user_context = f"""
        User's name: {current_user.profile.name}
        User's goal: {current_user.profile.goal}
        User's age: {current_user.profile.age if current_user.profile.age else 'Not specified'}
        """
        
        if len(chat_history) == 1:
            chat_history[0]['parts'][0] = f"{user_context}\n\nUser says: {chat_history[0]['parts'][0]}"
        
        ai_response = get_ai_chat_response(chat_history, detected_sentiment)
        
        ai_chat = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            role='model',
            content=ai_response
        )
        db.session.add(ai_chat)
        db.session.commit()
        
        response_data = {
            'response': ai_response,
            'success': True,
            'sentiment': detected_sentiment
        }
        
        if event_data:
            response_data['detected_event'] = event_data
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/save_journal', methods=['POST'])
@login_required
def save_journal():
    data = request.json
    mood = data.get('mood')
    summary = data.get('summary')
    
    if not mood or not summary:
        return jsonify({'error': 'Mood and summary are required'}), 400
    
    journal = Journal(
        user_id=current_user.id,
        mood=mood,
        summary=summary,
        goal_progress=''
    )
    db.session.add(journal)
    
    session_id = get_session_id()
    ChatMessage.query.filter_by(
        user_id=current_user.id,
        session_id=session_id
    ).delete()
    
    db.session.commit()
    
    session['chat_session_id'] = secrets.token_hex(16)
    session.modified = True
    
    return jsonify({'success': True, 'message': 'Journal entry saved!'})

@app.route('/get_summary', methods=['POST'])
@login_required
def get_summary():
    chat_history = get_chat_history_from_db()
    
    if not chat_history:
        return jsonify({'error': 'No chat history to summarize'}), 400
    
    try:
        full_chat_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'EmoAI'}: {msg['parts'][0]}"
            for msg in chat_history
        ])
        
        summary_prompt = f"""
        User's name: {current_user.profile.name}
        User's main goal: {current_user.profile.goal}
        
        {full_chat_text}
        """
        
        summary = summarize_chat_as_journal(summary_prompt)
        
        return jsonify({
            'summary': summary,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/journal')
@login_required
def journal_view():
    journals = Journal.query.filter_by(user_id=current_user.id).order_by(Journal.timestamp.desc()).all()
    return render_template('journal.html', journals=journals)

@app.route('/journal/analytics')
@login_required
def journal_analytics():
    """Journal analytics with graphs and AI insights"""
    journals = Journal.query.filter_by(user_id=current_user.id).order_by(Journal.timestamp.asc()).all()
    journals_data = [{
        'timestamp': j.timestamp.isoformat(),
        'mood': j.mood,
        'summary': j.summary,
        'goal_progress': j.goal_progress or ''
    } for j in journals]
    return render_template('journal_analytics.html', journals=journals, journals_data=journals_data)

@app.route('/clear_chat', methods=['POST'])
@login_required
def clear_chat():
    session_id = get_session_id()
    ChatMessage.query.filter_by(
        user_id=current_user.id,
        session_id=session_id
    ).delete()
    db.session.commit()
    
    session['chat_session_id'] = secrets.token_hex(16)
    session.modified = True
    return jsonify({'success': True})

# ========== HABIT REMINDER & PROGRESS ROUTES ==========

@app.route('/update_reminder_settings', methods=['POST'])
@login_required
def update_reminder_settings():
    """Update reminder enabled status and optional reminder time"""
    data = request.json
    enabled = data.get('enabled')
    reminder_time = data.get('reminder_time')
    
    if current_user.profile:
        if enabled is not None:
            current_user.profile.reminder_enabled = enabled
        if reminder_time is not None:
            current_user.profile.reminder_time = reminder_time
        db.session.commit()
        return jsonify({
            'success': True,
            'enabled': current_user.profile.reminder_enabled,
            'reminder_time': current_user.profile.reminder_time
        })
    return jsonify({'success': False}), 400

@app.route('/save_habit_progress', methods=['POST'])
@login_required
def save_habit_progress():
    """Save daily habit progress with optional note"""
    data = request.json
    progress_note = data.get('progress_note', '')
    
    today = date.today()
    
    # Check if progress already recorded today
    existing = HabitProgress.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    if existing:
        # Update existing entry
        existing.progress_note = progress_note
        existing.timestamp = datetime.utcnow()
    else:
        # Get latest mood from journal if available
        latest_journal = Journal.query.filter_by(
            user_id=current_user.id
        ).order_by(Journal.timestamp.desc()).first()
        
        mood = latest_journal.mood if latest_journal else None
        
        # Create new progress entry
        progress = HabitProgress(
            user_id=current_user.id,
            date=today,
            progress_note=progress_note,
            mood=mood
        )
        db.session.add(progress)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Progress saved!'})

@app.route('/get_reminder_status', methods=['GET'])
@login_required
def get_reminder_status():
    """Check if reminder should be shown today"""
    if not current_user.profile or not current_user.profile.reminder_enabled:
        return jsonify({'show_reminder': False})
    
    today = date.today()
    
    # Check if progress already recorded today
    existing = HabitProgress.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    # Get a random active reminder if available
    active_reminders = Reminder.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    if active_reminders:
        random_reminder = random.choice(active_reminders)
        reminder_message = random_reminder.message
    else:
        # Fallback to goal if no custom reminders
        reminder_message = f"How's your progress on: {current_user.profile.goal}?"
    
    return jsonify({
        'show_reminder': not existing,
        'user_name': current_user.profile.name,
        'reminder_message': reminder_message,
        'reminder_time': current_user.profile.reminder_time
    })

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page with 7-day habit streak visualization"""
    if not current_user.profile:
        return redirect(url_for('onboarding'))
    
    # Get last 7 days of progress
    today = date.today()
    seven_days_ago = today - timedelta(days=6)
    
    progress_records = HabitProgress.query.filter(
        HabitProgress.user_id == current_user.id,
        HabitProgress.date >= seven_days_ago
    ).order_by(HabitProgress.date.desc()).all()
    
    # Create a dictionary for easy lookup
    progress_dict = {p.date: p for p in progress_records}
    
    # Build 7-day streak data
    streak_data = []
    for i in range(6, -1, -1):
        check_date = today - timedelta(days=i)
        has_progress = check_date in progress_dict
        streak_data.append({
            'date': check_date,
            'day_name': check_date.strftime('%a'),
            'has_progress': has_progress,
            'progress': progress_dict.get(check_date)
        })
    
    # Calculate current streak
    current_streak = 0
    for day in reversed(streak_data):
        if day['has_progress']:
            current_streak += 1
        else:
            break
    
    # Auto-cleanup: Delete progress older than 30 days
    thirty_days_ago = today - timedelta(days=30)
    HabitProgress.query.filter(
        HabitProgress.user_id == current_user.id,
        HabitProgress.date < thirty_days_ago
    ).delete()
    db.session.commit()
    
    return render_template('dashboard.html', 
                         streak_data=streak_data,
                         current_streak=current_streak,
                         user_name=current_user.profile.name,
                         habit_goal=current_user.profile.goal)

@app.route('/delete_progress/<int:progress_id>', methods=['DELETE'])
@login_required
def delete_progress(progress_id):
    """Allow user to delete a specific progress entry"""
    progress = HabitProgress.query.filter_by(
        id=progress_id,
        user_id=current_user.id
    ).first()
    
    if progress:
        db.session.delete(progress)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Progress not found'}), 404

@app.route('/toggle_reminder', methods=['POST'])
@login_required
def toggle_reminder():
    if current_user.profile:
        current_user.profile.reminder_enabled = not current_user.profile.reminder_enabled
        db.session.commit()
        return jsonify({
            'success': True,
            'enabled': current_user.profile.reminder_enabled
        })
    return jsonify({'success': False}), 400

# ========== CUSTOM REMINDER MANAGEMENT ROUTES ==========

@app.route('/get_reminders', methods=['GET'])
@login_required
def get_reminders():
    """Get all reminders for the current user"""
    reminders = Reminder.query.filter_by(user_id=current_user.id).order_by(Reminder.created_at.desc()).all()
    return jsonify({
        'success': True,
        'reminders': [{
            'id': r.id,
            'message': r.message,
            'time': r.time,
            'is_active': r.is_active,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')
        } for r in reminders]
    })

@app.route('/create_reminder', methods=['POST'])
@login_required
def create_reminder():
    """Create a new custom reminder"""
    data = request.json
    message = data.get('message', '').strip()
    time = data.get('time')
    
    if not message:
        return jsonify({'success': False, 'error': 'Message is required'}), 400
    
    reminder = Reminder(
        user_id=current_user.id,
        message=message,
        time=time,
        is_active=True
    )
    db.session.add(reminder)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'reminder': {
            'id': reminder.id,
            'message': reminder.message,
            'time': reminder.time,
            'is_active': reminder.is_active,
            'created_at': reminder.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })

@app.route('/update_reminder/<int:reminder_id>', methods=['PUT'])
@login_required
def update_reminder(reminder_id):
    """Update an existing reminder"""
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first()
    
    if not reminder:
        return jsonify({'success': False, 'error': 'Reminder not found'}), 404
    
    data = request.json
    if 'message' in data:
        message = data['message'].strip()
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        reminder.message = message
    if 'time' in data:
        reminder.time = data['time']
    if 'is_active' in data:
        reminder.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'reminder': {
            'id': reminder.id,
            'message': reminder.message,
            'time': reminder.time,
            'is_active': reminder.is_active,
            'created_at': reminder.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })

@app.route('/delete_reminder/<int:reminder_id>', methods=['DELETE'])
@login_required
def delete_reminder(reminder_id):
    """Delete a reminder"""
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first()
    
    if not reminder:
        return jsonify({'success': False, 'error': 'Reminder not found'}), 404
    
    db.session.delete(reminder)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Reminder deleted'})

@app.route('/goals')
@login_required
def goals_page():
    """Goals management page"""
    goals = Goal.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('goals.html', goals=goals)

@app.route('/create_goal', methods=['POST'])
@login_required
def create_goal():
    """Create a new goal"""
    data = request.json
    title = data.get('title', '').strip()
    goal_type = data.get('goal_type', 'habit')
    description = data.get('description', '').strip()
    target_days = data.get('target_days', 30)
    
    if not title:
        return jsonify({'success': False, 'error': 'Title is required'}), 400
    
    goal = Goal(
        user_id=current_user.id,
        title=title,
        goal_type=goal_type,
        description=description,
        target_days=target_days,
        is_active=True
    )
    db.session.add(goal)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'goal': {
            'id': goal.id,
            'title': goal.title,
            'goal_type': goal.goal_type,
            'description': goal.description,
            'target_days': goal.target_days
        }
    })

@app.route('/log_activity', methods=['POST'])
@login_required
def log_activity():
    """Log an activity for a goal"""
    data = request.json
    
    goal_id = data.get('goal_id')
    activity_type = data.get('activity_type', '').strip()
    description = data.get('description', '').strip()
    
    if not goal_id:
        return jsonify({'success': False, 'error': 'Goal ID is required'}), 400
    
    if not activity_type:
        return jsonify({'success': False, 'error': 'Activity type is required'}), 400
    
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id, is_active=True).first()
    if not goal:
        return jsonify({'success': False, 'error': 'Goal not found or access denied'}), 404
    
    activity = Activity(
        goal_id=goal_id,
        user_id=current_user.id,
        date=date.today(),
        activity_type=activity_type,
        description=description,
        completed=True
    )
    db.session.add(activity)
    db.session.commit()
    
    motivation_msg = MotivationMessage(
        user_id=current_user.id,
        message=generate_motivation_message(activity_type),
        message_type='activity_completed',
        is_read=False
    )
    db.session.add(motivation_msg)
    db.session.commit()
    
    return jsonify({'success': True, 'motivation': motivation_msg.message})

@app.route('/sleep')
@login_required
def sleep_tracker():
    """Sleep tracking page"""
    sleep_logs = SleepLog.query.filter_by(user_id=current_user.id).order_by(SleepLog.date.desc()).limit(14).all()
    return render_template('sleep.html', sleep_logs=sleep_logs, user_name=current_user.profile.name if current_user.profile else 'User')

@app.route('/log_sleep', methods=['POST'])
@login_required
def log_sleep():
    """Log sleep data with AI analysis"""
    import ai_core_1762554001118 as ai_core
    
    data = request.json
    sleep_date = datetime.strptime(data.get('date', str(date.today())), '%Y-%m-%d').date()
    
    existing_log = SleepLog.query.filter_by(user_id=current_user.id, date=sleep_date).first()
    
    if existing_log:
        existing_log.bedtime = data.get('bedtime')
        existing_log.wake_time = data.get('wake_time')
        existing_log.hours_slept = data.get('hours_slept')
        existing_log.quality_rating = data.get('quality_rating')
        existing_log.notes = data.get('notes', '')
    else:
        sleep_log = SleepLog(
            user_id=current_user.id,
            date=sleep_date,
            bedtime=data.get('bedtime'),
            wake_time=data.get('wake_time'),
            hours_slept=data.get('hours_slept'),
            quality_rating=data.get('quality_rating'),
            notes=data.get('notes', '')
        )
        db.session.add(sleep_log)
    
    db.session.commit()
    
    recent_logs = SleepLog.query.filter_by(user_id=current_user.id).order_by(SleepLog.date.desc()).limit(7).all()
    
    ai_insights = None
    if recent_logs:
        try:
            sleep_data = [{
                'date': log.date.isoformat(),
                'hours': log.hours_slept,
                'quality': log.quality_rating,
                'bedtime': log.bedtime,
                'wake_time': log.wake_time,
                'notes': log.notes
            } for log in recent_logs]
            
            prompt = f"""Analyze this user's sleep data from the past week and provide personalized insights and recommendations.

Sleep Data:
{sleep_data}

Provide a brief analysis (2-3 sentences) covering:
1. Sleep patterns and trends
2. Quality assessment
3. One specific, actionable recommendation to improve sleep

Keep it warm, supportive, and feeling-first. No medical advice."""
            
            ai_insights = ai_core.get_ai_response_simple(prompt)
        except Exception as e:
            print(f"Error generating AI sleep insights: {e}")
    
    return jsonify({
        'success': True,
        'ai_insights': ai_insights
    })

@app.route('/get_motivations')
@login_required
def get_motivations():
    """Get unread motivation messages"""
    messages = MotivationMessage.query.filter_by(user_id=current_user.id, is_read=False).order_by(MotivationMessage.created_at.desc()).limit(5).all()
    return jsonify({
        'success': True,
        'motivations': [{
            'id': m.id,
            'message': m.message,
            'message_type': m.message_type,
            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
        } for m in messages]
    })

@app.route('/mark_motivation_read/<int:msg_id>', methods=['POST'])
@login_required
def mark_motivation_read(msg_id):
    """Mark motivation message as read"""
    msg = MotivationMessage.query.filter_by(id=msg_id, user_id=current_user.id).first()
    if msg:
        msg.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

def generate_motivation_message(activity_type):
    """Generate positive reinforcement messages"""
    messages = {
        'breathing': [
            "You're building such a powerful habit! Every breath brings more calm into your life.",
            "That's incredible progress! Your mind and body thank you for this moment of peace.",
            "You're doing amazing! Each breathing session strengthens your inner resilience."
        ],
        'walk': [
            "Way to go! Every step you take is a victory for your health and happiness.",
            "You're unstoppable! Your commitment to moving your body is truly inspiring.",
            "Fantastic work! You're building momentum one step at a time."
        ],
        'journal': [
            "Beautiful reflection! Your self-awareness is growing with each word you write.",
            "You're creating something meaningful! This practice is transforming you from within.",
            "Wonderful dedication! Journaling is one of the most powerful tools for growth."
        ],
        'meditation': [
            "Phenomenal! You're mastering the art of being present. This is real growth.",
            "You're glowing with progress! Each meditation deepens your inner peace.",
            "Incredible consistency! Your practice is building a foundation of calm strength."
        ],
        'exercise': [
            "You're crushing it! Your body is getting stronger, and so is your willpower.",
            "Absolutely amazing! You showed up for yourself today, and that's everything.",
            "You're on fire! Every workout brings you closer to your best self."
        ]
    }
    
    category_messages = messages.get(activity_type.lower(), [
        "Fantastic effort! You're making real progress toward your goals.",
        "You're doing wonderfully! Keep up this amazing momentum.",
        "Great work! Every positive action adds up to big transformations."
    ])
    
    return random.choice(category_messages)

@app.route('/my_calendar')
@login_required
def my_calendar():
    return render_template('my_calendar.html')

@app.route('/get_events', methods=['GET'])
@login_required
def get_events():
    """Get all events for the current user"""
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.event_date).all()
    return jsonify({
        'success': True,
        'events': [{
            'id': e.id,
            'title': e.title,
            'description': e.description,
            'date': e.event_date.isoformat(),
            'time': e.event_time,
            'location': e.location,
            'is_confirmed': e.is_confirmed,
            'is_in_google_calendar': e.is_in_google_calendar,
            'created_from_message': e.created_from_message
        } for e in events]
    })

@app.route('/confirm_event/<int:event_id>', methods=['POST'])
@login_required
def confirm_event(event_id):
    """Confirm and optionally edit an event"""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    import json
    
    event = Event.query.filter_by(id=event_id, user_id=current_user.id).first()
    if not event:
        return jsonify({'success': False, 'error': 'Event not found'}), 404
    
    data = request.json
    event.title = data.get('title', event.title)
    event.description = data.get('description', event.description)
    
    if data.get('date'):
        event.event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if 'time' in data:
        event.event_time = data['time']
    if 'location' in data:
        event.location = data['location']
    
    event.is_confirmed = True
    
    existing_reminder = Reminder.query.filter_by(
        user_id=current_user.id,
        message=f"Event: {event.title}"
    ).first()
    
    if existing_reminder:
        existing_reminder.time = event.event_time
        existing_reminder.is_active = True
    elif event.event_time:
        reminder = Reminder(
            user_id=current_user.id,
            message=f"Event: {event.title}",
            time=event.event_time,
            is_active=True
        )
        db.session.add(reminder)
    
    db.session.commit()
    
    token_record = GoogleCalendarToken.query.filter_by(user_id=current_user.id).first()
    if token_record and not event.is_in_google_calendar:
        try:
            creds = Credentials(
                token=token_record.access_token,
                refresh_token=token_record.refresh_token,
                token_uri=token_record.token_uri,
                client_id=token_record.client_id,
                client_secret=token_record.client_secret,
                scopes=json.loads(token_record.scopes) if token_record.scopes else []
            )
            
            service = build('calendar', 'v3', credentials=creds)
            
            event_body = {
                'summary': event.title,
                'description': event.description or '',
                'start': {
                    'date': event.event_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'date': event.event_date.isoformat(),
                    'timeZone': 'UTC',
                }
            }
            
            if event.event_time:
                start_datetime = f"{event.event_date.isoformat()}T{event.event_time}:00"
                event_body['start'] = {'dateTime': start_datetime, 'timeZone': 'UTC'}
                event_body['end'] = {'dateTime': start_datetime, 'timeZone': 'UTC'}
            
            if event.location:
                event_body['location'] = event.location
            
            calendar_event = service.events().insert(calendarId='primary', body=event_body).execute()
            
            event.is_in_google_calendar = True
            event.google_calendar_id = calendar_event['id']
            db.session.commit()
        except Exception as e:
            print(f"Error auto-syncing to Google Calendar: {e}")
    
    return jsonify({'success': True, 'event': {
        'id': event.id,
        'title': event.title,
        'date': event.event_date.isoformat(),
        'time': event.event_time,
        'location': event.location,
        'synced_to_google': event.is_in_google_calendar
    }})

@app.route('/update_event/<int:event_id>', methods=['PUT'])
@login_required
def update_event(event_id):
    """Update an existing event"""
    event = Event.query.filter_by(id=event_id, user_id=current_user.id).first()
    if not event:
        return jsonify({'success': False, 'error': 'Event not found'}), 404
    
    data = request.json
    
    if 'title' in data:
        event.title = data['title']
    if 'date' in data:
        event.event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if 'time' in data:
        event.event_time = data['time'] if data['time'] else None
    if 'location' in data:
        event.location = data['location'] if data['location'] else None
    if 'description' in data:
        event.description = data['description'] if data['description'] else None
    
    db.session.commit()
    return jsonify({'success': True, 'event': {
        'id': event.id,
        'title': event.title,
        'date': event.event_date.isoformat(),
        'time': event.event_time,
        'location': event.location,
        'description': event.description
    }})

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    """Delete an event"""
    event = Event.query.filter_by(id=event_id, user_id=current_user.id).first()
    if not event:
        return jsonify({'success': False, 'error': 'Event not found'}), 404
    
    db.session.delete(event)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/wellness_score', methods=['GET'])
@login_required
def wellness_score():
    """Calculate overall wellness score (0-100)"""
    from datetime import timedelta
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    mood_score = 0
    journal_entries = Journal.query.filter(
        Journal.user_id == current_user.id,
        Journal.timestamp >= datetime.combine(week_ago, datetime.min.time())
    ).all()
    
    if journal_entries:
        mood_values = {'happy': 100, 'grateful': 90, 'hopeful': 85, 'content': 80, 
                       'neutral': 70, 'anxious': 50, 'stressed': 40, 'sad': 30, 'frustrated': 20}
        avg_mood = sum(mood_values.get(j.mood.lower(), 70) for j in journal_entries) / len(journal_entries)
        mood_score = avg_mood * 0.25
    else:
        mood_score = 50 * 0.25
    
    sleep_score = 0
    sleep_logs = SleepLog.query.filter(
        SleepLog.user_id == current_user.id,
        SleepLog.date >= week_ago
    ).all()
    
    if sleep_logs:
        total_sleep_score = 0
        for log in sleep_logs:
            hours = log.hours_slept or 0
            quality = log.quality_rating or 3
            
            if 7 <= hours <= 9:
                duration_score = 50
            elif 6 <= hours < 7:
                duration_score = 40
            elif 9 < hours <= 10:
                duration_score = 45
            elif 5 <= hours < 6:
                duration_score = 30
            elif 4 <= hours < 5:
                duration_score = 20
            else:
                duration_score = 10
            
            quality_score = quality * 10
            log_score = min(duration_score + quality_score, 100)
            total_sleep_score += log_score
        
        avg_sleep = total_sleep_score / len(sleep_logs)
        sleep_score = avg_sleep * 0.25
    else:
        sleep_score = 50 * 0.25
    
    habit_score = 0
    goals = Goal.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    if goals:
        total_activities = 0
        for goal in goals:
            activities = Activity.query.filter(
                Activity.user_id == current_user.id,
                Activity.goal_id == goal.id,
                Activity.date >= week_ago,
                Activity.completed == True
            ).count()
            total_activities += activities
        
        habit_score = min((total_activities / 7) * 100, 100) * 0.25
    else:
        habit_score = 50 * 0.25
    
    journal_consistency_score = 0
    total_days = (today - month_ago).days
    if total_days > 0:
        all_month_journals = Journal.query.filter(
            Journal.user_id == current_user.id,
            Journal.timestamp >= datetime.combine(month_ago, datetime.min.time())
        ).count()
        
        consistency_pct = (all_month_journals / total_days) * 100
        journal_consistency_score = min(consistency_pct, 100) * 0.25
    else:
        journal_consistency_score = 50 * 0.25
    
    overall_score = int(mood_score + sleep_score + habit_score + journal_consistency_score)
    
    category_label = 'Excellent'
    if overall_score < 40:
        category_label = 'Needs Attention'
    elif overall_score < 60:
        category_label = 'Fair'
    elif overall_score < 80:
        category_label = 'Good'
    
    return jsonify({
        'success': True,
        'overall_score': overall_score,
        'category': category_label,
        'breakdown': {
            'mood': int(mood_score / 0.25),
            'sleep': int(sleep_score / 0.25),
            'habits': int(habit_score / 0.25),
            'journal_consistency': int(journal_consistency_score / 0.25)
        }
    })

@app.route('/calendar')
@login_required
def calendar_view():
    """Calendar dashboard page"""
    return render_template('calendar.html', user_name=current_user.profile.name if current_user.profile else 'User')

@app.route('/check_event_followups', methods=['GET'])
@login_required
def check_event_followups():
    """Check if there are any events from yesterday to follow up on"""
    yesterday = date.today() - timedelta(days=1)
    
    past_events = Event.query.filter(
        Event.user_id == current_user.id,
        Event.event_date == yesterday,
        Event.is_confirmed == True
    ).all()
    
    if past_events:
        event = past_events[0]
        return jsonify({
            'has_followup': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'date': event.event_date.isoformat()
            },
            'followup_message': f"How did your {event.title} go yesterday?"
        })
    
    return jsonify({'has_followup': False})

@app.route('/check_time_reminders', methods=['GET'])
@login_required
def check_time_reminders():
    """Check if any reminders should be shown based on current time"""
    if not current_user.profile or not current_user.profile.reminder_enabled:
        return jsonify({'show_reminder': False})
    
    from datetime import datetime as dt
    current_time = dt.now().strftime('%H:%M')
    
    active_reminders = Reminder.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    time_matched_reminders = [r for r in active_reminders if r.time and r.time == current_time[:5]]
    
    if time_matched_reminders:
        reminder = random.choice(time_matched_reminders)
        return jsonify({
            'show_reminder': True,
            'reminder': {
                'id': reminder.id,
                'message': reminder.message,
                'time': reminder.time
            }
        })
    
    if current_user.profile.reminder_time and current_user.profile.reminder_time == current_time[:5]:
        return jsonify({
            'show_reminder': True,
            'reminder': {
                'message': f"Time to check in on your goal: {current_user.profile.goal}"
            }
        })
    
    return jsonify({'show_reminder': False})

@app.route('/google_auth')
@login_required
def google_auth():
    from google_auth_oauthlib.flow import Flow
    
    client_config = {
        "web": {
            "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
            "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/google_callback"]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri=f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/google_callback"
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/google_callback')
@login_required
def google_callback():
    from google_auth_oauthlib.flow import Flow
    import json
    
    client_config = {
        "web": {
            "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
            "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/google_callback"]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/calendar'],
        state=session['oauth_state'],
        redirect_uri=f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/google_callback"
    )
    
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    
    existing_token = GoogleCalendarToken.query.filter_by(user_id=current_user.id).first()
    if existing_token:
        existing_token.access_token = credentials.token
        existing_token.refresh_token = credentials.refresh_token
        existing_token.token_uri = credentials.token_uri
        existing_token.client_id = credentials.client_id
        existing_token.client_secret = credentials.client_secret
        existing_token.scopes = json.dumps(credentials.scopes)
        existing_token.expiry = credentials.expiry
        existing_token.updated_at = datetime.utcnow()
    else:
        token = GoogleCalendarToken(
            user_id=current_user.id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=json.dumps(credentials.scopes),
            expiry=credentials.expiry
        )
        db.session.add(token)
    
    db.session.commit()
    flash('Successfully connected to Google Calendar!', 'success')
    return redirect(url_for('calendar'))

@app.route('/google_calendar_status')
@login_required
def google_calendar_status():
    token = GoogleCalendarToken.query.filter_by(user_id=current_user.id).first()
    return jsonify({
        'connected': token is not None,
        'expiry': token.expiry.isoformat() if token and token.expiry else None
    })

@app.route('/sync_event_to_google/<int:event_id>', methods=['POST'])
@login_required
def sync_event_to_google(event_id):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    import json
    
    event = Event.query.filter_by(id=event_id, user_id=current_user.id).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    token_record = GoogleCalendarToken.query.filter_by(user_id=current_user.id).first()
    if not token_record:
        return jsonify({'error': 'Google Calendar not connected'}), 400
    
    creds = Credentials(
        token=token_record.access_token,
        refresh_token=token_record.refresh_token,
        token_uri=token_record.token_uri,
        client_id=token_record.client_id,
        client_secret=token_record.client_secret,
        scopes=json.loads(token_record.scopes) if token_record.scopes else []
    )
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        event_body = {
            'summary': event.title,
            'description': event.description or '',
            'start': {
                'date': event.event_date.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'date': event.event_date.isoformat(),
                'timeZone': 'UTC',
            }
        }
        
        if event.event_time:
            start_datetime = f"{event.event_date.isoformat()}T{event.event_time}:00"
            event_body['start'] = {'dateTime': start_datetime, 'timeZone': 'UTC'}
            event_body['end'] = {'dateTime': start_datetime, 'timeZone': 'UTC'}
        
        if event.location:
            event_body['location'] = event.location
        
        calendar_event = service.events().insert(calendarId='primary', body=event_body).execute()
        
        event.is_in_google_calendar = True
        event.google_calendar_id = calendar_event['id']
        db.session.commit()
        
        return jsonify({
            'success': True,
            'google_event_id': calendar_event['id'],
            'google_event_link': calendar_event.get('htmlLink')
        })
    
    except Exception as e:
        print(f"Error syncing to Google Calendar: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
