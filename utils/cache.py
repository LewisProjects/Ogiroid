from functools import wraps

from aiocache import Cache, SimpleMemoryCache


def async_cache(maxsize=128):
    _cache = {}

    def decorator(func):
        @wraps(func)
        async def inner(*args, no_cache=False, **kwargs):
            if no_cache:
                return await func(*args, **kwargs)

            key_base = "_".join(str(x) for x in args)
            key_end = "_".join(f"{k}:{v}" for k, v in kwargs.items())
            key = f"{key_base}-{key_end}"

            if key in _cache:
                return _cache[key]

            res = await func(*args, **kwargs)

            if len(_cache) > maxsize:
                del _cache[list(_cache.keys())[0]]
                _cache[key] = res

            return res

        return inner

    return decorator


class AsyncTTL(SimpleMemoryCache):
    def __init__(self, ttl: int = 3600, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ttl = ttl

    async def get(self, key, *args, **kwargs):
        await super().expire(key, self.ttl)
        return await super().get(key, *args, **kwargs)

    async def set(self, key, value, *args, **kwargs):
        await super().set(key, value, ttl=self.ttl, *args, **kwargs)

    async def add(self, key, value, *args, **kwargs):
        await super().add(key, value, ttl=self.ttl, *args, **kwargs)


