from functools import wraps

from aiocache import SimpleMemoryCache


def async_cache(maxsize=128):
    """
    args:
        maxsize: int - the maximum size of the cache (default: 128) set to 0 for unlimited
    """
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

            if maxsize != 0:
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

    async def try_get(self, key):
        """
        Try to get a value from cache. If it's not there then it returns False.
        """
        value = await self.get(key, default=False)
        return value


    async def get(self, key, *args, **kwargs):
        await super().expire(key, self.ttl)
        return await super().get(key, *args, **kwargs)

    async def set(self, key, value, *args, **kwargs):
        await super().set(key, value, ttl=self.ttl, *args, **kwargs)

    async def add(self, key, value, *args, **kwargs):
        await super().add(key, value, ttl=self.ttl, *args, **kwargs)

    async def remove(self, key, *args, **kwargs):
        await super().delete(key, *args, **kwargs)
