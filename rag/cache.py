import hashlib
import json
import logging

import redis
from core.config import settings

logger = logging.getLogger(__name__)

cache = None
if settings.REDIS_CACHE_URL:
    try:
        cache = redis.Redis.from_url(
            settings.REDIS_CACHE_URL,
            decode_responses=True,
        )
    except Exception as err:
        logger.warning("Failed to initialize Redis cache client: %s", err)

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
    if cache is None:
        return None
    try:
        value = cache.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as err:
        logger.warning("Redis cache get failed (falling back to search): %s", err)
        return None

def set_cached_result(
        key : str,
        result,
        ttl : int = CACHE_TTL
):
    if cache is None:
        return
    try:
        cache.setex(
            key,
            ttl,
            json.dumps(result)
        )
    except Exception as err:
        logger.warning("Redis cache set failed: %s", err)