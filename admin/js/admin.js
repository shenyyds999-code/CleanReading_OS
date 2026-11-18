const API_BASE = '/api';

function getToken() { return localStorage.getItem('library_token') || ''; }
function getSavedUser() { try { return JSON.parse(localStorage.getItem('library_user') || 'null'); } catch { return null; } }
function saveToken(t) { localStorage.setItem('library_token', t); }
function saveUser(u) { localStorage.setItem('library_user', JSON.stringify(u)); }
function clearAuth() { localStorage.removeItem('library_token'); localStorage.removeItem('library_user'); }

function showToast(msg, type) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const id = 't' + Date.now();
    const bg = type === 'error' ? 'bg-danger' : 'bg-success';
    container.insertAdjacentHTML('beforeend',
        '<div id="' + id + '" class="toast align-items-center text-white ' + bg + ' border-0" role="alert"><div class="d-flex"><div class="toast-body">' + msg + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>');
    const el = document.getElementById(id);
    new bootstrap.Toast(el, { delay: 3000 }).show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
}

async function adminGet(url) {
    const resp = await fetch(API_BASE + url, {
        headers: { 'Authorization': 'Bearer ' + getToken() }
    });
    const data = await resp.json();
    if (data.code === 401 || data.code === 403) {
        clearAuth();
        window.location.href = 'login.html';
        return null;
    }
    return data;
}

async function adminPost(url, body) {
    const resp = await fetch(API_BASE + url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + getToken() },
        body: JSON.stringify(body)
    });
    const data = await resp.json();
    if (data.code === 401 || data.code === 403) {
        clearAuth();
        window.location.href = 'login.html';
        return null;
    }
    return data;
}

async function adminPut(url, body) {
    const resp = await fetch(API_BASE + url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + getToken() },
        body: JSON.stringify(body)
    });
    const data = await resp.json();
    if (data.code === 401 || data.code === 403) {
        clearAuth();
        window.location.href = 'login.html';
        return null;
    }
    return data;
}

async function adminDelete(url) {
    const resp = await fetch(API_BASE + url, {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer ' + getToken() }
    });
    const data = await resp.json();
    if (data.code === 401 || data.code === 403) {
        clearAuth();
        window.location.href = 'login.html';
        return null;
    }
    return data;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function getRoleName(role) {
    if (role === 3) return '<span class="badge bg-danger">超级管理员</span>';
    if (role === 2) return '<span class="badge bg-primary">图书管理员</span>';
    return '<span class="badge bg-secondary">读者</span>';
}

function checkAdminAuth() {
    const user = getSavedUser();
    if (!user || (user.role !== 2 && user.role !== 3)) {
        window.location.href = 'login.html';
        return null;
    }
    return user;
}

function loadSiteName() {
    fetch(API_BASE + '/system/config')
        .then(function (r) { return r.json(); })
        .then(function (data) {
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
        }).catch(function () {
            var els = document.querySelectorAll('.site-name');
            for (var i = 0; i < els.length; i++) els[i].style.visibility = 'visible';
        });
}

function applyAccentColor(hex) {
    hex = (hex || '#4b1e1e').trim();
    if (!/^#[0-9a-fA-F]{6}$/.test(hex) || hex.toLowerCase() === '#ff6699') hex = '#4b1e1e';

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

(function () {
    var style = document.createElement('style');
    style.textContent = '.site-name { color: var(--accent) !important; visibility: hidden; }';
    document.head.appendChild(style);
})();

(function () {
    try {
        var cached = localStorage.getItem('accent_color');
        if (cached) applyAccentColor(cached);
    } catch (e) {}
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadSiteName);
} else {
    loadSiteName();
}
