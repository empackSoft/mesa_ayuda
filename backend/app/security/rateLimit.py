import os
import time
import threading

import redis

# Límite de intentos (login, olvidé mi contraseña). Se guarda en Redis para que sobreviva
# reinicios del backend; si Redis no responde, se usa memoria del proceso.
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

_redis = redis.Redis.from_url(REDIS_URL, socket_timeout=1, socket_connect_timeout=1)
_memory = {}
_lock = threading.Lock()


def _memory_hits(key: str, window: int, add: bool) -> int:
    now = time.time()
    with _lock:
        hits = [t for t in _memory.get(key, []) if now - t < window]
        if add:
            hits.append(now)
        _memory[key] = hits
        return len(hits)


def register_hit(key: str, window: int) -> int:
    """Suma un intento a `key` y devuelve cuántos lleva dentro de la ventana (segundos)."""
    try:
        pipe = _redis.pipeline()
        pipe.incr(f"rl:{key}")
        pipe.expire(f"rl:{key}", window, nx=True)
        count, _ = pipe.execute()
        return int(count)
    except redis.RedisError:
        return _memory_hits(key, window, add=True)


def count_hits(key: str, window: int) -> int:
    try:
        value = _redis.get(f"rl:{key}")
        return int(value) if value else 0
    except redis.RedisError:
        return _memory_hits(key, window, add=False)


def retry_after(key: str, window: int) -> int:
    """Segundos que faltan para que se libere `key`."""
    try:
        ttl = _redis.ttl(f"rl:{key}")
        return max(int(ttl), 1) if ttl and ttl > 0 else window
    except redis.RedisError:
        with _lock:
            hits = _memory.get(key, [])
        return max(int(window - (time.time() - hits[0])), 1) if hits else window


def reset(key: str):
    try:
        _redis.delete(f"rl:{key}")
    except redis.RedisError:
        pass
    with _lock:
        _memory.pop(key, None)
