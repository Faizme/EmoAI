from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, UserProfile, Journal, ChatMessage
import os
import sys
import secrets
from datetime import datetime

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
    goal_progress = data.get('goal_progress', '')
    
    if not mood or not summary:
        return jsonify({'error': 'Mood and summary are required'}), 400
    
    journal = Journal(
        user_id=current_user.id,
        mood=mood,
        summary=summary,
        goal_progress=goal_progress
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
            f"{'User' if msg['role'] == 'user' else 'VILUN'}: {msg['parts'][0]}"
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
