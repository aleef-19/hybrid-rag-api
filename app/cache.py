import json
import redis

REDIS_URL = "redis://localhost:6379/0"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_cached_result(query: str, top_k: int):
    cache_key = f"search:{query.strip().lower()}:{top_k}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None

def set_cached_result(query: str, top_k: int, results: list, ttl: int = 3600):
    cache_key = f"search:{query.strip().lower()}:{top_k}"
    redis_client.setex(cache_key, ttl, json.dumps(results))

def clear_cache():
    redis_client.flushdb()