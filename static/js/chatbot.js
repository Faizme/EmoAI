const chatBox = document.getElementById('chatBox');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

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
    messageDiv.className = sender === 'user' ? 'user-message' : 'ai-message';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    if (sender === 'user') {
        bubble.innerHTML = `<strong>You:</strong> ${escapeHtml(message)}`;
    } else if (sender === 'ai') {
        bubble.innerHTML = `<strong>VILUN:</strong> ${escapeHtml(message)}`;
    } else {
        bubble.innerHTML = `<strong>Error:</strong> ${escapeHtml(message)}`;
        bubble.style.background = 'rgba(239, 68, 68, 0.2)';
        bubble.style.borderColor = 'rgba(239, 68, 68, 0.4)';
    }
    
    messageDiv.appendChild(bubble);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-message';
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
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
            document.getElementById('summaryModal').style.display = 'block';
        } else {
            alert(data.error || 'Failed to generate summary');
        }
    } catch (error) {
        alert('Failed to generate summary. Please try again.');
    }
}

function closeSummary() {
    document.getElementById('summaryModal').style.display = 'none';
}

function updateMoodEmoji() {
    const moodSelect = document.getElementById('moodSelect');
    const moodEmoji = document.getElementById('moodEmoji');
    const selectedMood = moodSelect.value;
    moodEmoji.textContent = selectedMood.split(' ')[0];
}

async function saveJournal() {
    const mood = document.getElementById('moodSelect').value;
    const summary = document.getElementById('summaryText').innerText;
    const goalProgress = document.getElementById('goalProgress').value;
    
    try {
        const response = await fetch('/save_journal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ mood, summary, goal_progress: goalProgress }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Journal entry saved successfully!');
            closeSummary();
            
            chatBox.innerHTML = `
                <div class="ai-message fade-in">
                    <div class="message-bubble">
                        <strong>VILUN:</strong> Great! Your journal entry has been saved. How else can I help you today?
                    </div>
                </div>
            `;
        } else {
            alert(data.error || 'Failed to save journal');
        }
    } catch (error) {
        alert('Failed to save journal. Please try again.');
    }
}

async function clearChat() {
    if (!confirm('Are you sure you want to start a new conversation?')) {
        return;
    }
    
    try {
        const response = await fetch('/clear_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        if (response.ok) {
            location.reload();
        }
    } catch (error) {
        alert('Failed to clear chat');
    }
}

function viewJournal() {
    window.location.href = '/journal';
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.onclick = function(event) {
    const modal = document.getElementById('summaryModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
    
    const progressModal = document.getElementById('progressForm');
    if (event.target === progressModal) {
        progressModal.classList.add('hidden');
    }
    
    const settingsModal = document.getElementById('reminderSettingsModal');
    if (event.target === settingsModal) {
        settingsModal.classList.add('hidden');
    }
}

// ========== REMINDER & HABIT PROGRESS FUNCTIONS ==========

// Check reminder status on page load
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/get_reminder_status');
        const data = await response.json();
        
        if (data.show_reminder) {
            // Update reminder popup with personalized message
            document.getElementById('reminderGreeting').textContent = `Hey ${data.user_name}! 👋`;
            document.getElementById('reminderMessage').textContent = 
                `Did you take one small step for your goal: "${data.habit_goal}" today?`;
            
            // Show reminder popup after a short delay
            setTimeout(() => {
                document.getElementById('reminderPopup').classList.remove('hidden');
            }, 1000);
        }
        
        // Load reminder settings
        await loadReminderSettings();
    } catch (error) {
        console.error('Failed to check reminder status:', error);
    }
});

function dismissReminder() {
    document.getElementById('reminderPopup').classList.add('hidden');
}

function showProgressForm() {
    document.getElementById('reminderPopup').classList.add('hidden');
    document.getElementById('progressForm').classList.remove('hidden');
    document.getElementById('progressForm').style.display = 'block';
}

function closeProgressForm() {
    document.getElementById('progressForm').classList.add('hidden');
    document.getElementById('progressForm').style.display = 'none';
    document.getElementById('progressNote').value = '';
}

async function saveProgress() {
    const progressNote = document.getElementById('progressNote').value.trim();
    
    if (!progressNote) {
        alert('Please write a short note about your progress!');
        return;
    }
    
    try {
        const response = await fetch('/save_habit_progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ progress_note: progressNote }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('🎉 Progress saved! Keep up the great work!');
            closeProgressForm();
        } else {
            alert('Failed to save progress. Please try again.');
        }
    } catch (error) {
        alert('Failed to save progress. Please try again.');
    }
}

// Reminder Settings Modal Functions
async function openReminderSettings() {
    await loadReminderSettings();
    document.getElementById('reminderSettingsModal').classList.remove('hidden');
    document.getElementById('reminderSettingsModal').style.display = 'block';
}

function closeReminderSettings() {
    document.getElementById('reminderSettingsModal').classList.add('hidden');
    document.getElementById('reminderSettingsModal').style.display = 'none';
}

async function loadReminderSettings() {
    try {
        const response = await fetch('/get_reminder_status');
        const data = await response.json();
        
        // Set toggle state
        const toggle = document.getElementById('reminderToggle');
        if (toggle) {
            toggle.checked = data.show_reminder !== false;
        }
        
        // Set time if available
        const timeInput = document.getElementById('reminderTime');
        if (timeInput && data.reminder_time) {
            timeInput.value = data.reminder_time;
        }
    } catch (error) {
        console.error('Failed to load reminder settings:', error);
    }
}

async function updateReminderToggle() {
    const enabled = document.getElementById('reminderToggle').checked;
    
    try {
        const response = await fetch('/update_reminder_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ enabled }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Reminder toggle updated:', data.enabled);
        }
    } catch (error) {
        console.error('Failed to update reminder toggle:', error);
    }
}

async function updateReminderTime() {
    const reminderTime = document.getElementById('reminderTime').value;
    
    try {
        const response = await fetch('/update_reminder_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ reminder_time: reminderTime }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Reminder time updated:', data.reminder_time);
        }
    } catch (error) {
        console.error('Failed to update reminder time:', error);
    }
}
