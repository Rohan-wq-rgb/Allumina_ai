const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:5000'
    : 'https://allumina-ai.onrender.com') + '/api';

const chatMessages = document.getElementById('chat-messages');
const emptyState = document.getElementById('empty-state');
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const fileInput = document.getElementById('file-upload');
const chatList = document.getElementById('chat-list');
const currentChatTitle = document.getElementById('current-chat-title');
const newChatBtn = document.getElementById('new-chat-btn');
const logoutBtn = document.getElementById('logout-btn');
const darkModeToggle = document.getElementById('dark-mode-toggle');
const toggleSidebar = document.getElementById('toggle-sidebar');
const sidebar = document.getElementById('sidebar');

let currentChatId = null;
let chats = [];

if (typeof marked !== 'undefined') {
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true
    });
}

async function checkSession() {
    try {
        const res = await fetch(`${API_BASE}/auth/session`, {
            credentials: 'include'
        });
        if (!res.ok) {
            window.location.href = 'login.html';
            return;
        }
        const data = await res.json();
        if (!data.logged_in) {
            window.location.href = 'login.html';
        }
    } catch (e) {
        window.location.href = 'login.html';
    }
}

async function loadChats() {
    try {
        const res = await fetch(`${API_BASE}/chats`, {
            credentials: 'include'
        });
        if (res.ok) {
            chats = await res.json();
            renderChatList();
        }
    } catch (e) {
        console.error('Failed to load chats:', e);
    }
}

function renderChatList() {
    chatList.innerHTML = chats.map(chat => `
        <div class="chat-list-item ${chat.id === currentChatId ? 'active' : ''}" data-id="${chat.id}">
            <span class="chat-title">${escapeHtml(chat.title)}</span>
            <button class="delete-chat btn-icon" data-id="${chat.id}">×</button>
        </div>
    `).join('');

    document.querySelectorAll('.chat-list-item .chat-title').forEach(el => {
        el.parentElement.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-chat')) return;
            const id = parseInt(el.parentElement.dataset.id);
            openChat(id);
        });
    });

    document.querySelectorAll('.delete-chat').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            await deleteChat(id);
        });
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function openChat(chatId) {
    currentChatId = chatId;
    try {
        const res = await fetch(`${API_BASE}/chats/${chatId}/messages`, {
            credentials: 'include'
        });
        if (!res.ok) return;
        const data = await res.json();
        currentChatTitle.textContent = data.title || 'Chat';
        renderMessages(data.messages);
        loadChats();
    } catch (e) {
        console.error('Failed to open chat:', e);
    }
}

async function deleteChat(chatId) {
    try {
        await fetch(`${API_BASE}/chats/${chatId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        if (currentChatId === chatId) {
            currentChatId = null;
            currentChatTitle.textContent = 'New Chat';
            chatMessages.innerHTML = '';
            emptyState.style.display = 'flex';
        }
        loadChats();
    } catch (e) {
        console.error('Failed to delete chat:', e);
    }
}

function renderMessages(messages) {
    emptyState.style.display = 'none';
    chatMessages.innerHTML = messages.map(msg => `
        <div class="message-bubble ${msg.role}">
            ${msg.role === 'assistant' && typeof marked !== 'undefined' ? marked.parse(msg.content) : escapeHtml(msg.content)}
        </div>
    `).join('');
    chatMessages.scrollTop = chatMessages.scrollHeight;

    document.querySelectorAll('pre code').forEach(block => {
        if (typeof hljs !== 'undefined') {
            hljs.highlightElement(block);
        }
    });
}

messageForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = messageInput.value.trim();
    if (!message) return;

    const formData = new FormData();
    formData.append('message', message);
    if (fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
    }

    let endpoint;
    if (!currentChatId) {
        endpoint = `${API_BASE}/chats`;
    } else {
        endpoint = `${API_BASE}/chats/${currentChatId}/messages`;
    }

    const userBubble = document.createElement('div');
    userBubble.className = 'message-bubble user';
    userBubble.textContent = message;
    chatMessages.appendChild(userBubble);
    emptyState.style.display = 'none';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    messageInput.value = '';
    fileInput.value = '';

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        if (!res.ok) throw new Error('Failed to send message');

        const data = await res.json();

        if (data.chat_id) {
            currentChatId = data.chat_id;
            currentChatTitle.textContent = data.title;
            loadChats();

            const msgsRes = await fetch(`${API_BASE}/chats/${currentChatId}/messages`, {
                credentials: 'include'
            });
            if (msgsRes.ok) {
                const fullData = await msgsRes.json();
                renderMessages(fullData.messages);
            }
        } else {
            const assistantBubble = document.createElement('div');
            assistantBubble.className = 'message-bubble assistant';
            assistantBubble.innerHTML = typeof marked !== 'undefined'
                ? marked.parse(data.assistant_message.content)
                : escapeHtml(data.assistant_message.content);
            chatMessages.appendChild(assistantBubble);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            document.querySelectorAll('pre code').forEach(block => {
                if (typeof hljs !== 'undefined') {
                    hljs.highlightElement(block);
                }
            });
        }
    } catch (err) {
        userBubble.remove();
        alert('Error: ' + err.message);
    }
});

document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        messageInput.value = chip.textContent;
        messageForm.dispatchEvent(new Event('submit'));
    });
});

newChatBtn.addEventListener('click', () => {
    currentChatId = null;
    currentChatTitle.textContent = 'New Chat';
    chatMessages.innerHTML = '';
    emptyState.style.display = 'flex';
    loadChats();
});

logoutBtn.addEventListener('click', async () => {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
    } catch (e) {
        console.error('Logout error:', e);
    }
    window.location.href = 'login.html';
});

darkModeToggle.addEventListener('click', () => {
    const isDark = document.body.getAttribute('data-theme') === 'dark';
    if (isDark) {
        document.body.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
    } else {
        document.body.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    }
});

toggleSidebar.addEventListener('click', () => {
    sidebar.classList.toggle('open');
});

if (localStorage.getItem('theme') === 'dark') {
    document.body.setAttribute('data-theme', 'dark');
}

checkSession();
loadChats();
