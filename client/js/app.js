const API_BASE = '/api';
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

function loadSiteName() {
    fetch(API_BASE + '/system/config')
        .then(r => r.json())
        .then(data => {
            if (data.code === 200 && data.data.site_name) {
                var name = data.data.site_name;
                document.title = document.title.replace(/校园图书馆/g, name);
                var els = document.querySelectorAll('.site-name');
                for (var i = 0; i < els.length; i++) {
                    els[i].textContent = name;
                    els[i].style.visibility = 'visible';
                }
            } else {
                var els = document.querySelectorAll('.site-name');
                for (var i = 0; i < els.length; i++) els[i].style.visibility = 'visible';
            }
        }).catch(function() {
            var els = document.querySelectorAll('.site-name');
            for (var i = 0; i < els.length; i++) els[i].style.visibility = 'visible';
        });
}

(function () {
    var style = document.createElement('style');
    style.textContent = '.site-name { color: var(--accent) !important; visibility: hidden; }';
    document.head.appendChild(style);
})();

function applyAccentColor(hex) {
    hex = (hex || '#FF6699').trim();
    if (!/^#[0-9a-fA-F]{6}$/.test(hex)) hex = '#FF6699';

    var r = parseInt(hex.slice(1, 3), 16);
    var g = parseInt(hex.slice(3, 5), 16);
    var b = parseInt(hex.slice(5, 7), 16);

    var hr = Math.max(0, r - 35);
    var hg = Math.max(0, g - 17);
    var hb = Math.max(0, b - 25);
    var hover = '#' + [hr, hg, hb].map(function (v) { return v.toString(16).padStart(2, '0'); }).join('');

    var accentVars = [
        ':root {',
        '--accent: ' + hex + ';',
        '--accent-hover: ' + hover + ';',
        '--accent-alpha25: rgba(' + r + ',' + g + ',' + b + ',0.25);',
        '--accent-alpha15: rgba(' + r + ',' + g + ',' + b + ',0.15);',
        '--accent-alpha10: rgba(' + r + ',' + g + ',' + b + ',0.1);',
        '}'
    ].join('');

    var existing = document.getElementById('accent-style');
    if (existing) existing.remove();

    var style = document.createElement('style');
    style.id = 'accent-style';
    style.textContent = accentVars;
    document.head.appendChild(style);

    try { localStorage.setItem('accent_color', hex); } catch (e) {}
}

function getAccentColor() {
    try { return localStorage.getItem('accent_color') || '#FF6699'; } catch (e) { return '#FF6699'; }
}

function loadAccentColor() {
    var cached = getAccentColor();
    applyAccentColor(cached);

    if (!isLoggedIn()) return;

    fetch(API_BASE + '/user/settings', { headers: getDefaultHeaders() })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.code === 200 && data.data.theme_color) {
                applyAccentColor(data.data.theme_color);
            }
        }).catch(function () {});
}

loadAccentColor();
loadSiteName();

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
