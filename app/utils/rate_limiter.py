import time
import functools
from flask import current_app, request
from app.utils.cache import get_cache, cache_incr, cache_get, cache_set, CacheKey, SimpleCache
from app.utils.response import error


def parse_rate_limit(limit_str):
    parts = limit_str.strip().split('/')
    if len(parts) != 2:
        return 60, 60
    max_req = int(parts[0])
    unit = parts[1].lower()
    if unit == 'second':
        window = 1
    elif unit == 'minute':
        window = 60
    elif unit == 'hour':
        window = 3600
    else:
        window = 60
    return max_req, window


def _get_client_key():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        client_ip = forwarded.split(',')[0].strip()
    else:
        client_ip = request.remote_addr or '127.0.0.1'
    return client_ip


def rate_limit(max_requests=None, per_window=None, limit_str=None, key_func=None):
    if limit_str:
        max_requests, per_window = parse_rate_limit(limit_str)

    if max_requests is None:
        max_requests = 60
    if per_window is None:
        per_window = 60

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if not current_app.config.get('RATE_LIMIT_ENABLED', False):
                return f(*args, **kwargs)

            client_key = key_func() if key_func else _get_client_key()
            endpoint = request.endpoint or f.__name__
            rate_key = CacheKey.RATE_LIMIT(endpoint + ':' + client_key, str(int(time.time() / per_window)))

            current_count = cache_incr(rate_key, 1, per_window)

            remaining = max_requests - current_count
            if remaining < 0:
                remaining = 0

            if current_count > max_requests:
                return error(429, '请求过于频繁，请稍后再试', http_status=429)

            response = f(*args, **kwargs)
            try:
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = str(max_requests)
                    response.headers['X-RateLimit-Remaining'] = str(remaining)
                    response.headers['X-RateLimit-Reset'] = str(int(time.time() / per_window + 1) * per_window)
            except Exception:
                pass
            return response
        return wrapper
    return decorator
