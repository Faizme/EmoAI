// Chat Elements
const chatBox = document.getElementById('chatBox');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');

// Voice Recognition Setup
let recognition = null;
let isListening = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
        isListening = true;
        voiceBtn.classList.add('listening');
    };
    
    recognition.onend = () => {
        isListening = false;
        voiceBtn.classList.remove('listening');
    };
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        sendMessage();
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isListening = false;
        voiceBtn.classList.remove('listening');
    };
}

function toggleVoiceInput() {
    if (!recognition) {
        alert('Voice input is not supported in your browser. Please use Chrome, Safari, or Edge.');
        return;
    }
    
    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

// Text-to-Speech for AI responses
let voiceEnabled = localStorage.getItem('voiceEnabled') !== 'false';

function speakText(text) {
    if (voiceEnabled && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.pitch = 1.05;
        utterance.volume = 0.9;
        
        const voices = window.speechSynthesis.getVoices();
        const femaleVoice = voices.find(voice => 
            voice.name.includes('Female') || 
            voice.name.includes('Samantha') ||
            voice.name.includes('Karen') ||
            voice.name.includes('Victoria')
        );
        if (femaleVoice) {
            utterance.voice = femaleVoice;
        }
        
        window.speechSynthesis.speak(utterance);
    }
}

function toggleVoiceResponse() {
    voiceEnabled = !voiceEnabled;
    localStorage.setItem('voiceEnabled', voiceEnabled);
    
    const toggleBtn = document.getElementById('voiceToggleBtn');
    const toggleText = document.getElementById('voiceToggleText');
    
    if (voiceEnabled) {
        toggleBtn.classList.remove('voice-off');
        toggleText.textContent = 'Voice On';
    } else {
        toggleBtn.classList.add('voice-off');
        toggleText.textContent = 'Voice Off';
        window.speechSynthesis.cancel();
    }
}

window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices();
};

// Enter key to send
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;
    
    addMessageToChat('user', message);
    userInput.value = '';
    sendBtn.disabled = true;
    
    const typingIndicator = addTypingIndicator();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });
        
        const data = await response.json();
        
        typingIndicator.remove();
        
        if (data.success) {
            addMessageToChat('ai', data.response);
            speakText(data.response);
        } else {
            addMessageToChat('error', data.error || 'Something went wrong');
        }
    } catch (error) {
        typingIndicator.remove();
        addMessageToChat('error', 'Failed to connect. Please try again.');
    }
    
    sendBtn.disabled = false;
    userInput.focus();
}

function addMessageToChat(sender, message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' ? 'user-message-elegant' : 'ai-message-elegant';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageSender = document.createElement('div');
    messageSender.className = 'message-sender';
    messageSender.textContent = sender === 'user' ? 'YOU' : 'EMOAI';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = message;
    
    if (sender === 'error') {
        messageSender.textContent = 'ERROR';
        messageContent.style.background = 'rgba(239, 68, 68, 0.1)';
        messageContent.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    }
    
    messageContent.appendChild(messageSender);
    messageContent.appendChild(messageText);
    messageDiv.appendChild(messageContent);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-message-elegant';
    typingDiv.innerHTML = `
        <div class="typing-indicator-elegant">
            <div class="typing-dot-elegant"></div>
            <div class="typing-dot-elegant"></div>
            <div class="typing-dot-elegant"></div>
        </div>
    `;
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return typingDiv;
}

async function getSummary() {
    try {
        const response = await fetch('/get_summary', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('summaryText').innerText = data.summary;
            document.getElementById('summaryModal').classList.remove('hidden');
        } else {
            alert(data.error || 'Failed to generate summary');
        }
    } catch (error) {
        alert('Failed to generate summary. Please try again.');
    }
}

function closeSummary() {
    document.getElementById('summaryModal').classList.add('hidden');
}

async function saveJournal() {
    const mood = document.getElementById('moodSelect').value;
    const summary = document.getElementById('summaryText').innerText;
    
    try {
        const response = await fetch('/save_journal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ mood, summary }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            closeSummary();
            clearChat();
        } else {
            alert('Failed to save journal entry');
        }
    } catch (error) {
        alert('Failed to save journal entry. Please try again.');
    }
}

async function clearChat() {
    if (!confirm('Start a new conversation? This will clear your current chat.')) return;
    
    try {
        const response = await fetch('/clear_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        const data = await response.json();
        
        if (data.success) {
            chatBox.innerHTML = `
                <div class="ai-message-elegant fade-in">
                    <div class="message-content">
                        <div class="message-sender">EMOAI</div>
                        <div class="message-text">Hello! How are you feeling today?</div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error clearing chat:', error);
    }
}

function viewJournal() {
    window.location.href = '/journal';
}

function logout() {
    window.location.href = '/logout';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Reminder functionality
async function checkReminderStatus() {
    try {
        const response = await fetch('/get_reminder_status');
        const data = await response.json();
        
        if (data.reminder_enabled && data.show_popup) {
            showReminderPopup(data.reminder_message, data.user_name);
        }
    } catch (error) {
        console.error('Error checking reminder status:', error);
    }
}

function showReminderPopup(message, userName) {
    document.getElementById('reminderGreeting').textContent = `Hey ${userName}!`;
    document.getElementById('reminderMessage').textContent = message;
    document.getElementById('reminderPopup').classList.remove('hidden');
}

function dismissReminder() {
    document.getElementById('reminderPopup').classList.add('hidden');
    markReminderAsSeen();
}

async function markReminderAsSeen() {
    try {
        await fetch('/mark_reminder_seen', { method: 'POST' });
    } catch (error) {
        console.error('Error marking reminder as seen:', error);
    }
}

function showProgressForm() {
    document.getElementById('reminderPopup').classList.add('hidden');
    document.getElementById('progressForm').classList.remove('hidden');
}

function closeProgressForm() {
    document.getElementById('progressForm').classList.add('hidden');
    document.getElementById('progressNote').value = '';
}

async function saveProgress() {
    const note = document.getElementById('progressNote').value.trim();
    
    if (!note) {
        alert('Please write something about your progress');
        return;
    }
    
    try {
        const response = await fetch('/save_progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ progress_note: note }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Progress saved! Keep up the great work!');
            closeProgressForm();
            markReminderAsSeen();
        } else {
            alert('Failed to save progress');
        }
    } catch (error) {
        alert('Failed to save progress. Please try again.');
    }
}

function openReminderSettings() {
    document.getElementById('reminderSettingsModal').classList.remove('hidden');
    loadReminderSettings();
    loadReminders();
}

function closeReminderSettings() {
    document.getElementById('reminderSettingsModal').classList.add('hidden');
}

async function loadReminderSettings() {
    try {
        const response = await fetch('/get_reminder_settings');
        const data = await response.json();
        
        document.getElementById('reminderToggle').checked = data.reminder_enabled;
        document.getElementById('reminderTime').value = data.reminder_time || '';
    } catch (error) {
        console.error('Error loading reminder settings:', error);
    }
}

async function updateReminderToggle() {
    const enabled = document.getElementById('reminderToggle').checked;
    
    try {
        await fetch('/update_reminder_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ reminder_enabled: enabled }),
        });
    } catch (error) {
        console.error('Error updating reminder toggle:', error);
    }
}

async function updateReminderTime() {
    const time = document.getElementById('reminderTime').value;
    
    try {
        await fetch('/update_reminder_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ reminder_time: time }),
        });
    } catch (error) {
        console.error('Error updating reminder time:', error);
    }
}

async function loadReminders() {
    try {
        const response = await fetch('/get_reminders');
        const data = await response.json();
        
        const remindersList = document.getElementById('remindersList');
        
        if (data.reminders && data.reminders.length > 0) {
            remindersList.innerHTML = data.reminders.map(reminder => `
                <div class="reminder-card ${!reminder.is_active ? 'inactive' : ''}">
                    <div class="reminder-text">
                        <div>${escapeHtml(reminder.message)}</div>
                        ${reminder.time ? `<small>Time: ${reminder.time}</small>` : ''}
                    </div>
                    <div class="reminder-actions">
                        <button class="elegant-btn btn-outline" onclick="toggleReminder(${reminder.id}, ${!reminder.is_active})">
                            ${reminder.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button class="elegant-btn btn-outline" onclick="deleteReminder(${reminder.id})">Delete</button>
                    </div>
                </div>
            `).join('');
        } else {
            remindersList.innerHTML = '<p class="loading-text">No reminders yet</p>';
        }
    } catch (error) {
        console.error('Error loading reminders:', error);
    }
}

async function createReminder() {
    const message = document.getElementById('newReminderMessage').value.trim();
    const time = document.getElementById('newReminderTime').value;
    
    if (!message) {
        alert('Please enter a reminder message');
        return;
    }
    
    try {
        const response = await fetch('/create_reminder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message, time }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('newReminderMessage').value = '';
            document.getElementById('newReminderTime').value = '';
            loadReminders();
        } else {
            alert('Failed to create reminder');
        }
    } catch (error) {
        alert('Failed to create reminder. Please try again.');
    }
}

async function toggleReminder(id, activate) {
    try {
        const response = await fetch('/toggle_reminder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ reminder_id: id, is_active: activate }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadReminders();
        }
    } catch (error) {
        console.error('Error toggling reminder:', error);
    }
}

async function deleteReminder(id) {
    if (!confirm('Delete this reminder?')) return;
    
    try {
        const response = await fetch(`/delete_reminder/${id}`, {
            method: 'DELETE',
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadReminders();
        }
    } catch (error) {
        console.error('Error deleting reminder:', error);
    }
}

// Check reminder status on page load
window.addEventListener('DOMContentLoaded', () => {
    checkReminderStatus();
});
