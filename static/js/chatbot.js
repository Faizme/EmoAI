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
}
