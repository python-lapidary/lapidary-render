import logging
from collections.abc import Iterable, Sequence
from importlib.metadata import version
from pathlib import Path

import platformdirs
import yaml
from jsonpatch import JsonPatch

from .config import Config
from .load import load_yaml_cached

logger = logging.getLogger(__name__)


def load_spec(schema_path: Path, patches: Iterable[Path], config: Config) -> dict:
    cache_path = platformdirs.user_cache_path('lapidary', version=version('lapidary'))
    cache_path.mkdir(parents=True, exist_ok=True)

    logger.info('Load schema')
    spec_dict = load_yaml_cached(schema_path, cache_path, config.cache)

    if (patch := load_patches(patches, cache_path, config)) is not None:
        spec_dict = patch.apply(spec_dict)

    return spec_dict


def load_patches(patches: Sequence[Path], cache_path, config: Config) -> JsonPatch | None:
    if not patches:
        return None
    first = patches[0]
    if first.is_dir() and len(patches) != 1:
        raise ValueError('Patches must be either a single directory, or one or more files')

    if first.is_dir():
        patches = first.glob('**/*.[yamljson]')

    logger.info('Load patches')
    return JsonPatch([
        op
        for p in patches
        if p.suffix in ('yaml', 'yml', 'json')
        for op in load_yaml_cached(p, cache_path, config.cache)
    ])


def save_spec(doc: dict, path: Path) -> None:
    with open(path, 'wt') as stream:
        yaml.safe_dump(doc, stream, allow_unicode=True)
