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
                for (var i = 0; i < els.length; i++) { els[i].textContent = name; }
            }
        }).catch(function () { });
}

(function () {
    var style = document.createElement('style');
    style.textContent = '.site-name { color: #FF6699 !important; }';
    document.head.appendChild(style);
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadSiteName);
} else {
    loadSiteName();
}
