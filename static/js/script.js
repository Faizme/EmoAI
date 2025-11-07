const chatBox = document.getElementById('chatBox');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const summaryBox = document.getElementById('summaryBox');
const summaryContent = document.getElementById('summaryContent');

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
  
  const thinkingDiv = addThinkingIndicator();
  
  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
    
    const data = await response.json();
    
    if (thinkingDiv) {
      thinkingDiv.remove();
    }
    
    if (data.success) {
      addMessageToChat('vilun', data.response);
    } else {
      addMessageToChat('error', data.error || 'Something went wrong. Please try again.');
    }
  } catch (error) {
    if (thinkingDiv) {
      thinkingDiv.remove();
    }
    addMessageToChat('error', 'Failed to connect. Please check if the server is running.');
  }
  
  sendBtn.disabled = false;
  userInput.focus();
}

function addMessageToChat(sender, message) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}-message`;
  
  if (sender === 'user') {
    messageDiv.innerHTML = `<div class="message-content"><strong>You:</strong> ${escapeHtml(message)}</div>`;
  } else if (sender === 'vilun') {
    messageDiv.innerHTML = `<div class="message-content"><strong>VILUN:</strong> ${escapeHtml(message)}</div>`;
  } else if (sender === 'error') {
    messageDiv.innerHTML = `<div class="message-content error"><strong>Error:</strong> ${escapeHtml(message)}</div>`;
  }
  
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function addThinkingIndicator() {
  const thinkingDiv = document.createElement('div');
  thinkingDiv.className = 'message vilun-message thinking';
  thinkingDiv.innerHTML = '<div class="message-content"><strong>VILUN:</strong> <span class="typing">typing...</span></div>';
  chatBox.appendChild(thinkingDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
  return thinkingDiv;
}

async function generateSummary() {
  try {
    const response = await fetch('/summarize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const data = await response.json();
    
    if (data.success) {
      summaryContent.innerHTML = `<p>${escapeHtml(data.summary).replace(/\n/g, '<br>')}</p>`;
      summaryBox.style.display = 'block';
    } else {
      alert(data.error || 'Failed to generate summary');
    }
  } catch (error) {
    alert('Failed to connect to the server');
  }
}

function closeSummary() {
  summaryBox.style.display = 'none';
}

async function clearChat() {
  if (!confirm('Are you sure you want to start a new conversation? This will clear your chat history.')) {
    return;
  }
  
  try {
    const response = await fetch('/clear', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      chatBox.innerHTML = `
        <div class="welcome-message">
          <p>👋 Hi! I'm VILUN, your friendly companion.</p>
          <p>I'm here to listen and be supportive. How are you feeling today?</p>
        </div>
      `;
    }
  } catch (error) {
    alert('Failed to clear chat');
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
