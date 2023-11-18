import shutil
from uuid import uuid4
import os

# Module level variable to track if the cache directory has been created
_cache_dir_created = False
_cache_dir = None


def get_cache_dir():
    global _cache_dir_created, _cache_dir
    if not _cache_dir_created:
        _cache_dir = f".cache/{uuid4()}"
        os.makedirs(_cache_dir, exist_ok=True)
        _cache_dir_created = True
    return _cache_dir


def cleanup_cache_dir(cache_dir):
    shutil.rmtree(cache_dir)
