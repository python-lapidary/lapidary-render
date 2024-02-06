import hashlib
import logging
import pickle
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_yaml_cached(path: Path, cache_root: Path, use_cache: bool) -> dict:
    text = path.read_text()
    return load_yaml_cached_(text, cache_root, use_cache)


def load_yaml_cached_(text: str, cache_root: Path, use_cache: bool) -> dict:
    do_cache = use_cache and len(text) > 50_000
    if do_cache:
        digest = hashlib.sha224(text.encode()).hexdigest()
        cache_path = (cache_root / digest).with_suffix('.pickle' + str(pickle.HIGHEST_PROTOCOL))
        if cache_path.exists():
            with cache_path.open('br') as fb:
                return pickle.load(fb)

    d = yaml.safe_load(text)
    if do_cache:
        with cache_path.open('bw') as fb:
            pickle.dump(d, fb, pickle.HIGHEST_PROTOCOL)

    return d
