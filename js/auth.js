const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:5000'
    : 'https://allumina-ai.onrender.com') + '/api/auth';

let isLoginMode = true;

const form = document.getElementById('auth-form');
const title = document.getElementById('auth-title');
const subtitle = document.getElementById('auth-subtitle');
const switchText = document.getElementById('switch-text');
const switchLink = document.getElementById('switch-link');
const submitBtn = document.getElementById('auth-submit-btn');
const messageDiv = document.getElementById('auth-message');

function toggleMode() {
    isLoginMode = !isLoginMode;
    if (isLoginMode) {
        title.textContent = 'Welcome back';
        subtitle.textContent = 'Sign in to continue';
        submitBtn.textContent = 'Sign In';
        switchText.textContent = 'No account?';
        switchLink.textContent = 'Sign up';
    } else {
        title.textContent = 'Create account';
        subtitle.textContent = 'Start your journey';
        submitBtn.textContent = 'Sign Up';
        switchText.textContent = 'Already have an account?';
        switchLink.textContent = 'Sign in';
    }
}

switchLink.addEventListener('click', (e) => {
    e.preventDefault();
    toggleMode();
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    if (!email || !password) return;

    const endpoint = isLoginMode ? `${API_BASE}/login` : `${API_BASE}/signup`;
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Request failed');
        messageDiv.className = 'message success';
        messageDiv.textContent = data.message;
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);
    } catch (err) {
        messageDiv.className = 'message error';
        messageDiv.textContent = err.message;
    }
});

async function checkSession() {
    try {
        const res = await fetch(`${API_BASE}/session`, {
            credentials: 'include'
        });
        const data = await res.json();
        if (data.logged_in) {
            window.location.href = 'index.html';
        }
    } catch (e) {
    }
}

checkSession();
