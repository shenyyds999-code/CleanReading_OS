import time
import threading
import functools
import json
from collections import OrderedDict
from flask import current_app, request


class SimpleCache:
    def __init__(self):
        self._store = OrderedDict()
        self._lock = threading.RLock()

    def _clean_expired(self):
        now = time.time()
        expired = [k for k, (_, expires) in self._store.items() if expires and expires < now]
        for k in expired:
            del self._store[k]

    def get(self, key):
        with self._lock:
            self._clean_expired()
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires = entry
            if expires and expires < time.time():
                del self._store[key]
                return None
            return value

    def set(self, key, value, ttl=None):
        with self._lock:
            expires = time.time() + ttl if ttl else None
            self._store[key] = (value, expires)
            while len(self._store) > 10000:
                self._store.popitem(last=False)

    def delete(self, key):
        with self._lock:
            self._store.pop(key, None)

    def exists(self, key):
        with self._lock:
            self._clean_expired()
            entry = self._store.get(key)
            if entry is None:
                return False
            value, expires = entry
            if expires and expires < time.time():
                del self._store[key]
                return False
            return True

    def incr(self, key, amount=1, ttl=None):
        with self._lock:
            self._clean_expired()
            entry = self._store.get(key)
            current = 0
            if entry is not None:
                val, expires = entry
                if expires is None or expires >= time.time():
                    current = val
                else:
                    del self._store[key]
            value = current + amount
            expires = time.time() + ttl if ttl else None
            self._store[key] = (value, expires)
            return value

    def keys(self, pattern='*'):
        with self._lock:
            self._clean_expired()
            return [k for k in self._store if pattern == '*' or pattern in k]

    def flush(self):
        with self._lock:
            self._store.clear()


def _get_redis_client():
    import redis as redis_lib
    redis_url = current_app.config.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
    connect_timeout = current_app.config.get('REDIS_CONNECT_TIMEOUT', 3)
    socket_timeout = current_app.config.get('REDIS_SOCKET_TIMEOUT', 2)
    return redis_lib.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=connect_timeout,
        socket_timeout=socket_timeout
    )


def get_cache():
    fallback = getattr(current_app, '_cache_fallback', None)
    if fallback:
        return fallback

    if not current_app.config.get('REDIS_ENABLED', False):
        fallback = SimpleCache()
        current_app._cache_fallback = fallback
        return fallback

    client = getattr(current_app, '_redis_client', None)
    if client is None:
        try:
            client = _get_redis_client()
            client.ping()
            current_app._redis_client = client
        except Exception:
            import warnings
            warnings.warn('Redis 连接失败，降级为内存缓存')
            fallback = SimpleCache()
            current_app._redis_client = None
            current_app._cache_fallback = fallback
            return fallback

    return client


def invalidate_cache():
    cache = get_cache()
    if isinstance(cache, SimpleCache):
        cache.flush()
    else:
        cache.flushdb()


class CacheKey:
    PREFIX = 'lib'

    @staticmethod
    def make(*parts):
        return ':'.join([CacheKey.PREFIX] + list(parts))

    USER = staticmethod(lambda uid: CacheKey.make('user', str(uid)))
    USER_TOKEN_BLACKLIST = staticmethod(lambda jti: CacheKey.make('jwt', 'blacklist', jti))
    BOOK = staticmethod(lambda bid: CacheKey.make('book', str(bid)))
    BOOK_LIST = staticmethod(lambda q, page, search_type='fuzzy', per_page=20: CacheKey.make(
        'books', 'list', q or '_', str(page), search_type, str(per_page)))
    RATE_LIMIT = staticmethod(lambda key, window: CacheKey.make('rate', key, str(window)))


def cache_get(key, default=None):
    cache = get_cache()
    try:
        if isinstance(cache, SimpleCache):
            return cache.get(key)
        raw = cache.get(key)
        if raw is None:
            return default
        # Redis 中统一以 JSON 字符串存储
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return raw
    except Exception:
        return default


def cache_set(key, value, ttl=None):
    if ttl is None:
        ttl = current_app.config.get('CACHE_DEFAULT_TTL', 300)
    cache = get_cache()
    try:
        if isinstance(cache, SimpleCache):
            cache.set(key, value, ttl)
        else:
            cache.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        pass


def cache_delete_prefix(prefix):
    """按前缀批量清理缓存，用于图书库存、评分等联动失效。"""
    cache = get_cache()
    try:
        if isinstance(cache, SimpleCache):
            for key in cache.keys(prefix):
                cache.delete(key)
        else:
            for key in cache.scan_iter(match=f'{prefix}*'):
                cache.delete(key)
    except Exception:
        pass


def cache_delete(key):
    cache = get_cache()
    try:
        if isinstance(cache, SimpleCache):
            cache.delete(key)
        else:
            cache.delete(key)
    except Exception:
        pass


def cache_exists(key):
    cache = get_cache()
    try:
        if isinstance(cache, SimpleCache):
            return cache.exists(key)
        return bool(cache.exists(key))
    except Exception:
        return False


def cache_incr(key, amount=1, ttl=None):
    cache = get_cache()
    try:
        if isinstance(cache, SimpleCache):
            return cache.incr(key, amount, ttl)
        if ttl:
            pipe = cache.pipeline()
            pipe.incrby(key, amount)
            pipe.expire(key, ttl)
            result = pipe.execute()
            return result[0]
        return cache.incrby(key, amount)
    except Exception:
        return 0


def cache_keys(pattern='*'):
    cache = get_cache()
    try:
        if isinstance(cache, SimpleCache):
            return cache.keys(pattern)
        full_pattern = f'{CacheKey.PREFIX}:{pattern}' if not pattern.startswith(CacheKey.PREFIX) else pattern
        return list(cache.scan_iter(match=full_pattern))
    except Exception:
        return []


def cache_result(prefix, ttl=None):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            key_parts = [prefix]
            for a in args:
                if isinstance(a, (str, int, float)):
                    key_parts.append(str(a))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f'{k}={v}')
            cache_key = CacheKey.make(*key_parts)

            cached = cache_get(cache_key)
            if cached is not None:
                return cached

            result = f(*args, **kwargs)
            if result is not None:
                cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def cache_invalidate(prefix):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            pattern = f'{CacheKey.PREFIX}:{prefix}*'
            for key in cache_keys(pattern):
                cache_delete(key)
            return result
        return wrapper
    return decorator
