const API_BASE = '/api';
const TOKEN_KEY = 'kiosk_token';
const USER_KEY = 'kiosk_user';
const CLIENT_TYPE = 'kiosk';

function getToken() {
    return localStorage.getItem(TOKEN_KEY) || '';
}

function getSavedUser() {
    try {
        const user = localStorage.getItem(USER_KEY);
        return user ? JSON.parse(user) : null;
    } catch (e) {
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
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    }
    headers['X-Client-Type'] = CLIENT_TYPE;
    return headers;
}

async function apiGet(url) {
    const response = await fetch(API_BASE + url, {
        method: 'GET',
        headers: getDefaultHeaders()
    });
    const data = await response.json();
    if (data.code === 401 || data.code === 403) {
        clearAuth();
        window.location.href = '/kiosk/';
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
    if (data.code === 401 || data.code === 403) {
        clearAuth();
        window.location.href = '/kiosk/';
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
            <div class="toast-body fs-4">${msg}</div>
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
        if (currentPage !== 'index.html' && currentPage !== '' && currentPage !== '/') {
            window.location.href = '/kiosk/';
        }
        return null;
    }
    return getSavedUser();
}

(function () {
    try {
        var cached = localStorage.getItem('accent_color');
        if (cached && /^#[0-9a-fA-F]{6}$/.test(cached)) {
            var r = parseInt(cached.slice(1, 3), 16);
            var g = parseInt(cached.slice(3, 5), 16);
            var b = parseInt(cached.slice(5, 7), 16);
            var hr = Math.max(0, r - 35);
            var hg = Math.max(0, g - 17);
            var hb = Math.max(0, b - 25);
            var hover = '#' + [hr, hg, hb].map(function (v) { return v.toString(16).padStart(2, '0'); }).join('');
            var style = document.createElement('style');
            style.id = 'accent-style';
            style.textContent = ':root { --accent: ' + cached + '; --accent-hover: ' + hover + '; }';
            document.head.appendChild(style);
        }
    } catch (e) {}
})();
