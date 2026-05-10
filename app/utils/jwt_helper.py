import uuid
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request
from app.models import User
from app.utils.response import error
from app.utils.cache import cache_get, cache_set, cache_exists, CacheKey


def generate_token(user):
    jti = str(uuid.uuid4())
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'jti': jti,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24),
        'iat': datetime.now(timezone.utc)
    }
    from flask import current_app
    secret = current_app.config.get('JWT_SECRET_KEY', 'dev-jwt-secret')
    return jwt.encode(payload, secret, algorithm='HS256')


def _parse_token_from_header():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, '未提供有效的认证令牌'
    return auth_header[7:], None


def _verify_token():
    token, err = _parse_token_from_header()
    if err:
        return None, err

    try:
        from flask import current_app
        secret = current_app.config.get('JWT_SECRET_KEY', 'dev-jwt-secret')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None, '登录已过期，请重新登录'
    except jwt.InvalidTokenError:
        return None, '无效的认证令牌'

    jti = payload.get('jti', '')
    if jti:
        blacklist_key = CacheKey.USER_TOKEN_BLACKLIST(jti)
        if cache_exists(blacklist_key):
            return None, '令牌已失效，请重新登录'

    user = User.query.get(payload['user_id'])
    if not user:
        return None, '用户不存在或已被禁用'
    return user, None


def _get_token_jti():
    token, err = _parse_token_from_header()
    if err or not token:
        return None
    try:
        from flask import current_app
        secret = current_app.config.get('JWT_SECRET_KEY', 'dev-jwt-secret')
        payload = jwt.decode(token, secret, algorithms=['HS256'],
                            options={'verify_exp': False})
        return payload.get('jti', '')
    except Exception:
        return None


def revoke_current_token():
    jti = _get_token_jti()
    if jti:
        from flask import current_app
        blacklist_key = CacheKey.USER_TOKEN_BLACKLIST(jti)
        ttl = current_app.config.get('JWT_EXPIRATION_HOURS', 24) * 3600
        cache_set(blacklist_key, '1', ttl)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, err = _verify_token()
        if err:
            return error(401, err)
        return f(current_user=user, *args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, err = _verify_token()
        if err:
            return error(401, err)
        if user.role not in (2, 3):
            return error(403, '需要管理员权限')
        return f(current_user=user, *args, **kwargs)
    return decorated


def super_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, err = _verify_token()
        if err:
            return error(401, err)
        if user.role != 3:
            return error(403, '需要超级管理员权限')
        return f(current_user=user, *args, **kwargs)
    return decorated
