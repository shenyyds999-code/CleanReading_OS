from functools import wraps
from flask import request
from app.utils.response import error

KIOSK_ALLOWED_PREFIXES = [
    '/api/auth/login',
    '/api/auth/register',
    '/api/auth/me',
    '/api/auth/logout',
    '/api/borrow',
    '/api/books',
    '/api/health',
]


def kiosk_blocked(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        client_type = request.headers.get('X-Client-Type', '')
        if client_type.lower() == 'kiosk':
            path = request.path
            allowed = any(path.startswith(p) for p in KIOSK_ALLOWED_PREFIXES)
            if not allowed:
                return error(403, '借书机端不支持此操作')
        return f(*args, **kwargs)
    return decorated
