document.addEventListener('DOMContentLoaded', function() {
  // --- Tab Toggle Logic ---
  console.log("Script loaded. Document ready.");
  const assistantTab = document.getElementById('assistantTab');
  const chatTab = document.getElementById('chatTab');
  console.log("assistantTab:", assistantTab, "chatTab:", chatTab);

  const assistantSection = document.getElementById('assistantSection');
  const chatSection = document.getElementById('chatSection');

  assistantTab.addEventListener('click', (e) => {
    e.preventDefault();
    assistantTab.classList.add('active');
    chatTab.classList.remove('active');
    assistantSection.style.display = 'block';
    chatSection.style.display = 'none';
  });

  chatTab.addEventListener('click', (e) => {
    e.preventDefault();
    console.log('Chat Model tab clicked'); // Debug log
    chatTab.classList.add('active');
    assistantTab.classList.remove('active');
    assistantSection.style.display = 'none';
    chatSection.style.display = 'block';
  });

  // --- AI Assistant (Excel Upload & Q&A) Logic ---
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const chatContainer = document.getElementById('chatContainer');
  const progressBar = document.getElementById('uploadProgress');
  const progress = progressBar.querySelector('.progress');

  dropZone.querySelector('.browse-link').addEventListener('click', () => {
    fileInput.click();
  });

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
      handleFile(e.target.files[0]);
    }
  });

  async function handleFile(file) {
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      showNotification('Please upload an Excel file (.xlsx or .xls)', 'error');
      return;
    }

    // Clear previous messages
    chatContainer.innerHTML = '';

    const formData = new FormData();
    formData.append('file', file);

    progressBar.hidden = false;
    progress.style.width = '30%';

    const thinkingMessage = createMessageElement(
      'response',
      'Processing your questions. This may take a moment...',
      'AI'
    );
    chatContainer.appendChild(thinkingMessage);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      chatContainer.removeChild(thinkingMessage);

      if (data.status === 'success') {
        progress.style.width = '100%';
        setTimeout(() => {
          progressBar.hidden = true;
          progress.style.width = '0%';
        }, 1000);

        displayResponses(data.responses);
        showNotification('File processed successfully!', 'success');
      } else {
        showNotification('Error: ' + data.message, 'error');
        progressBar.hidden = true;
        progress.style.width = '0%';
      }
    } catch (error) {
      if (chatContainer.contains(thinkingMessage)) {
        chatContainer.removeChild(thinkingMessage);
      }
      showNotification('Error uploading file: ' + error.message, 'error');
      progressBar.hidden = true;
      progress.style.width = '0%';
    }
  }

  function displayResponses(responses) {
    if (!responses || responses.length === 0) {
      const emptyMessage = document.createElement('div');
      emptyMessage.className = 'empty-message';
      emptyMessage.textContent = 'No questions found in the uploaded file. Please ensure your Excel file contains a "questions" column.';
      chatContainer.appendChild(emptyMessage);
      return;
    }
    
    let delay = 0;
    responses.forEach(({ question, response, source }) => {
      setTimeout(() => {
        const questionDiv = createMessageElement(
          'question',
          question,
          'User'
        );
        chatContainer.appendChild(questionDiv);
        questionDiv.scrollIntoView({ behavior: 'smooth' });
      }, delay);
      delay += 300;
      setTimeout(() => {
        const responseDiv = createMessageElement(
          'response',
          response,
          source || 'AI Assistant'
        );
        chatContainer.appendChild(responseDiv);
        responseDiv.scrollIntoView({ behavior: 'smooth' });
      }, delay);
      delay += 300;
    });
  }

  function createMessageElement(type, text, source) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', type);

    const icon = document.createElement('img');
    icon.src = type === 'question' ? '/static/images/user.png' : '/static/images/robot.png';
    icon.alt = type === 'question' ? 'User' : 'AI';
    icon.className = 'message-icon';

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');

    const p = document.createElement('p');
    p.textContent = text;
    contentDiv.appendChild(p);

    if (type === 'response' && source) {
      const sourceTag = document.createElement('div');
      sourceTag.className = 'source-tag';
      sourceTag.textContent = `Source: ${source}`;
      contentDiv.appendChild(sourceTag);
    }

    messageDiv.appendChild(icon);
    messageDiv.appendChild(contentDiv);
    return messageDiv;
  }

  function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 5000);
  }

  const notificationStyles = document.createElement('style');
  notificationStyles.textContent = `
    .notification {
      position: fixed;
      bottom: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 4px;
      background-color: var(--primary-color);
      color: white;
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
      transform: translateY(20px);
      opacity: 0;
      transition: all 0.3s ease;
      z-index: 1000;
      max-width: 300px;
    }
    .notification.show {
      transform: translateY(0);
      opacity: 1;
    }
    .notification.success {
      background-color: var(--success-color);
    }
    .notification.error {
      background-color: #e74c3c;
    }
  `;
  document.head.appendChild(notificationStyles);

  // --- Chat Model Logic ---
  const chatModelContainer = document.getElementById('chatModelContainer');
  const chatModelInput = document.getElementById('chatModelInput');
  const chatModelSendBtn = document.getElementById('chatModelSendBtn');

  if (chatModelSendBtn) {
    chatModelSendBtn.addEventListener('click', async () => {
      const userMessage = chatModelInput.value.trim();
      if (!userMessage) return;
      addChatBubble(chatModelContainer, userMessage, 'question');
      chatModelInput.value = '';
      try {
        const response = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userMessage })
        });
        if (!response.ok) {
          throw new Error(`Server responded with ${response.status}`);
        }
        const data = await response.json();
        addChatBubble(chatModelContainer, data.response, 'response');
      } catch (error) {
        console.error('Error in chat model:', error);
        addChatBubble(chatModelContainer, 'Sorry, something went wrong.', 'response');
      }
    });
  }

  function addChatBubble(container, text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', type);

    const icon = document.createElement('img');
    icon.src = type === 'question' ? '/static/images/user.png' : '/static/images/robot.png';
    icon.alt = type === 'question' ? 'User' : 'AI';
    icon.classList.add('message-icon');

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');

    const p = document.createElement('p');
    p.textContent = text;
    contentDiv.appendChild(p);

    messageDiv.appendChild(icon);
    messageDiv.appendChild(contentDiv);
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
  }
});
