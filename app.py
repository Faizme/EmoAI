from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, UserProfile, Journal, ChatMessage, HabitProgress, Reminder, Goal, Activity, MotivationMessage, SleepLog
import os
import sys
import secrets
import random
from datetime import datetime, date, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), 'attached_assets'))
from ai_core_1762554001118 import get_ai_chat_response, summarize_chat_as_journal

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
        chat_history = get_chat_history_from_db()
        
        user_context = f"""
        User's name: {current_user.profile.name}
        User's goal: {current_user.profile.goal}
        User's age: {current_user.profile.age if current_user.profile.age else 'Not specified'}
        """
        
        if len(chat_history) == 1:
            chat_history[0]['parts'][0] = f"{user_context}\n\nUser says: {chat_history[0]['parts'][0]}"
        
        ai_response = get_ai_chat_response(chat_history)
        
        ai_chat = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            role='model',
            content=ai_response
        )
        db.session.add(ai_chat)
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'success': True
        })
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
    """Log sleep data"""
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
    return jsonify({'success': True})

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
