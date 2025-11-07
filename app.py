from flask import Flask, render_template, request, jsonify
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'attached_assets'))
from ai_core_1762554001118 import get_ai_chat_response, summarize_chat_as_journal

app = Flask(__name__, static_folder='.', static_url_path='', template_folder='.')

chat_history = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    chat_history.append({
        'role': 'user',
        'parts': [user_message]
    })
    
    try:
        ai_response = get_ai_chat_response(chat_history)
        
        chat_history.append({
            'role': 'model',
            'parts': [ai_response]
        })
        
        return jsonify({
            'response': ai_response,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/summarize', methods=['POST'])
def summarize():
    if not chat_history:
        return jsonify({'error': 'No chat history to summarize'}), 400
    
    try:
        full_chat_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'VILUN'}: {msg['parts'][0]}"
            for msg in chat_history
        ])
        
        summary = summarize_chat_as_journal(full_chat_text)
        
        return jsonify({
            'summary': summary,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    global chat_history
    chat_history = []
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
