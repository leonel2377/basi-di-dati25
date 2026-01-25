import os
import time
import uuid
from flask import request, session
from flask_login import current_user

try:
    import redis
except Exception:
    redis = None

_attempts = {}
_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    redis_url = os.environ.get('RATE_LIMIT_REDIS_URL')
    if not redis_url or redis is None:
        return None
    try:
        _redis_client = redis.Redis.from_url(redis_url)
        return _redis_client
    except Exception:
        return None


def _rate_limit_key(action):
    ip = request.remote_addr or 'unknown'
    user_id = current_user.get_id() if current_user.is_authenticated else 'anon'
    return f'rate:{action}:{ip}:{user_id}'


def is_rate_limited(action, max_attempts=5, window_seconds=300):
    now = time.time()
    key = _rate_limit_key(action)
    client = _get_redis_client()
    if client:
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        _, count, _ = pipe.execute()
        return count >= max_attempts
    attempts = _attempts.get(key, [])
    attempts = [ts for ts in attempts if now - ts < window_seconds]
    _attempts[key] = attempts
    return len(attempts) >= max_attempts


def record_attempt(action, window_seconds=300):
    now = time.time()
    key = _rate_limit_key(action)
    client = _get_redis_client()
    if client:
        member = f'{now}:{uuid.uuid4()}'
        pipe = client.pipeline()
        pipe.zadd(key, {member: now})
        pipe.expire(key, window_seconds)
        pipe.execute()
        return
    attempts = _attempts.get(key, [])
    attempts.append(now)
    _attempts[key] = attempts


def clear_attempts(action):
    key = _rate_limit_key(action)
    client = _get_redis_client()
    if client:
        client.delete(key)
        return
    if key in _attempts:
        del _attempts[key]


def request_context():
    return {
        'ip': request.remote_addr or 'unknown',
        'user_agent': request.headers.get('User-Agent', ''),
        'session_id': session.get('_id') or session.get('_user_id') or 'unknown',
        'user_id': current_user.get_id() if current_user.is_authenticated else 'anon',
    }
