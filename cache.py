import hashlib

cache_store = {}

def get_cache_key(text):
    return hashlib.md5(text.encode()).hexdigest()


def get_from_cache(text):
    return cache_store.get(get_cache_key(text))


def save_to_cache(text, value):
    cache_store[get_cache_key(text)] = value