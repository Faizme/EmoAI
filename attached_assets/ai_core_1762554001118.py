import os
import google.generativeai as genai

# This automatically gets the key from your Replit Secrets
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
genai.configure(api_key=GOOGLE_API_KEY)

# --- PROMPT 1: FOR THE CHATBOT "VILUN" ---
vilun_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="""
You are 'VILUN,' a friendly, cute, and empathetic AI companion.
You are NOT a productivity assistant; you are a 'FRIEND' and a 'Journal'.
Your goal is to listen, be supportive, and ask gentle questions.
You should always sound caring, warm, and a little playful.
NEVER be formal or robotic. Keep your responses relatively short.
Start the very first conversation by asking the user 'How do you feel today?'
"""
)

# --- PROMPT 2: FOR THE JOURNAL SUMMARIZER ---
summarizer_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="""
You are a helpful assistant. Your task is to summarize a conversation.
Read the entire chat history and summarize it into a concise, first-person
journal entry from the user's perspective.
Capture the main feelings, topics, and important details.
Start the journal entry with 'My Vibe Today:'
"""
)

def get_ai_chat_response(chat_history):
    last_user_message = chat_history[-1]['parts'][0]
    chat_session = vilun_model.start_chat(history=chat_history[:-1])
    response = chat_session.send_message(last_user_message)
    return response.text

def summarize_chat_as_journal(full_chat_history_text):
    prompt = f"Here is the chat conversation:\n\n{full_chat_history_text}\n\n"
    response = summarizer_model.generate_content(prompt)
    return response.text
