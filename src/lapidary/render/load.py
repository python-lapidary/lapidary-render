import hashlib
import logging
import pickle
from pathlib import Path

import yaml

from .model.openapi import model as openapi
from .model.python import ClientModel, get_client_model
from .model.python.module_path import ModulePath
from .model.refs import get_resolver

logger = logging.getLogger(__name__)


def load_yaml_cached(path: Path, cache_root: Path, use_cache: bool) -> dict:
    with open(path, 'rt') as fb:
        text = fb.read()

    return load_yaml_cached_(text, cache_root, use_cache)


def load_yaml_cached_(text: str, cache_root: Path, use_cache: bool) -> dict:
    do_cache = use_cache and len(text) > 50_000
    if do_cache:
        digest = hashlib.sha224(text.encode()).hexdigest()
        cache_path = (cache_root / digest).with_suffix('.pickle' + str(pickle.HIGHEST_PROTOCOL))
        if cache_path.exists():
            with open(cache_path, 'br') as fb:
                return pickle.load(fb)

    d = yaml.safe_load(text)
    if do_cache:
        with open(cache_path, 'bw') as fb:
            pickle.dump(d, fb, pickle.HIGHEST_PROTOCOL)

    return d


def load_model(mod: str) -> openapi.OpenApiModel:
    from importlib.resources import open_text

    logger.debug("Loading OpenAPI from %s", mod)
    with open_text(mod, 'openapi.yaml') as stream:
        text = stream.read()

    import platformdirs
    d = load_yaml_cached_(text, platformdirs.user_cache_path(), True)
    return openapi.OpenApiModel.parse_obj(d)


def get_model(package: ModulePath) -> ClientModel:
    openapi_model = load_model(str(package))
    return get_client_model(openapi_model, package, get_resolver(openapi_model, str(package)))
