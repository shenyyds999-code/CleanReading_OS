const API_BASE = 'http://127.0.0.1:5000/api';
const TOKEN_KEY = 'library_token';
const USER_KEY = 'library_user';

function getToken() {
    return localStorage.getItem(TOKEN_KEY) || '';
}

function getSavedUser() {
    try {
        const user = localStorage.getItem(USER_KEY);
        return user ? JSON.parse(user) : null;
    } catch {
        return null;
    }
}

function saveToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function saveUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

function isLoggedIn() {
    return !!getToken();
}

function getDefaultHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };
    const token = getToken();
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    }
    return headers;
}

async function apiGet(url) {
    const response = await fetch(API_BASE + url, {
        method: 'GET',
        headers: getDefaultHeaders()
    });
    const data = await response.json();
    if (data.code === 401) {
        clearAuth();
        window.location.href = '/client/login.html';
        return null;
    }
    return data;
}

async function apiPost(url, body) {
    const response = await fetch(API_BASE + url, {
        method: 'POST',
        headers: getDefaultHeaders(),
        body: JSON.stringify(body)
    });
    const data = await response.json();
    if (data.code === 401) {
        clearAuth();
        window.location.href = '/client/login.html';
        return null;
    }
    return data;
}

function showToast(msg, type) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const bgClass = type === 'success' ? 'bg-success' :
                    type === 'error' ? 'bg-danger' :
                    type === 'warning' ? 'bg-warning text-dark' : 'bg-info';

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white ${bgClass} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${msg}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    container.appendChild(toastEl);

    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

function checkAuthAndRedirect() {
    if (!isLoggedIn()) {
        const currentPage = window.location.pathname.split('/').pop();
        if (currentPage !== 'login.html' && currentPage !== 'register.html') {
            window.location.href = '/client/login.html';
        }
        return null;
    }

    const pageless = ['login.html', 'register.html'];
    const currentPage = window.location.pathname.split('/').pop();
    if (pageless.includes(currentPage)) {
        window.location.href = '/client/index.html';
        return null;
    }

    return getSavedUser();
}
