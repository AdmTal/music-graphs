import shutil
from uuid import uuid4
import os
import hashlib

# Module level variable to track if the cache directory has been created
_cache_dir_created = False
_cache_dir = None

_music_cache_base_dir = ".cache/.music_cache"
os.makedirs(_music_cache_base_dir, exist_ok=True)


def get_cache_dir():
    global _cache_dir_created, _cache_dir
    if not _cache_dir_created:
        _cache_dir = f".cache/{uuid4()}"
        os.makedirs(_cache_dir, exist_ok=True)
        _cache_dir_created = True
    return _cache_dir


def cleanup_cache_dir(cache_dir):
    shutil.rmtree(cache_dir)


def get_music_cache_dir(midi_file_path):
    with open(midi_file_path, 'rb') as f:
        midi_data = f.read()
        midi_hash = hashlib.sha256(midi_data).hexdigest()

    cache_dir = os.path.join(_music_cache_base_dir, midi_hash)
    os.makedirs(cache_dir, exist_ok=True)

    return cache_dir
