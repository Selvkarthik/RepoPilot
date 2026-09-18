import hashlib
import json
import os

import redis
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_CACHE_URL")

if not redis_url:
    raise RuntimeError("Redis cache configuration is missing.")

cache = redis.Redis.from_url(
    redis_url,
    decode_responses = True,
)

CACHE_TTL = 3600

def build_cache_key(
        repository : str,
        commit_sha : str,
        query : str
) -> str:

    normalized_query = query.strip().lower()

    raw_key = (
        f"{repository}:"
        f"{commit_sha}:"
        f"{normalized_query}:"
    )

    query_hash = hashlib.sha256(
        raw_key.encode('utf-8')
    ).hexdigest()

    return f"repopilot:search:{query_hash}"

def get_cached_result(key : str):
    value = cache.get(key)

    if value is None:
        return None

    return json.loads(value)

def set_cached_result(
        key : str,
        result,
        ttl : int = CACHE_TTL
):
    cache.setex(
        key,
        ttl,
        json.dumps(result)
    )