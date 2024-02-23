import abc
import hashlib
import logging
import pickle
from collections.abc import Mapping, Sequence
from typing import Self, cast

import httpx
import platformdirs
import ruamel.yaml
from anyio import Path
from jsonpatch import JsonPatch

from .config import Config

type JSON = str | int | float | Mapping[str, Self] | Sequence[Self] | None


logger = logging.getLogger(__name__)


async def load_document(root: Path, config: Config, cache: bool) -> JSON:
    cache_root = Path(platformdirs.user_cache_path('lapidary'))

    logger.info('Load OpenAPI document')
    spec_dict = await load_parse(config.document_path, cache, cache_root)

    if (patch := await load_patches(root / config.patches, cache, cache_root)) is not None:
        spec_dict = patch.apply(cast(dict, spec_dict))

    return spec_dict


async def load_parse(path: str | Path, cache: bool, cache_root: Path) -> JSON:
    text, _ = await get_document_text(path)
    if cache:
        return await parse_cache(text, cache_root)
    else:
        return parse(text)


async def parse_cache(text: str, cache_root: Path) -> JSON:
    digest = hashlib.sha224(text.encode()).hexdigest()
    cache_path = Path((cache_root / digest).with_suffix('.pickle' + str(pickle.HIGHEST_PROTOCOL)))
    if await cache_path.exists():
        b = await cache_path.read_bytes()
        return pickle.loads(b)
    else:
        d = parse(text)
        await cache_root.mkdir(parents=True, exist_ok=True)
        await cache_path.write_bytes(pickle.dumps(d, pickle.HIGHEST_PROTOCOL))


def parse(text: str) -> JSON:
    yaml = ruamel.yaml.YAML(typ='safe')
    return yaml.load(text)


async def load_patches(project_root: Path, cache: bool, cache_root: Path) -> JsonPatch | None:
    patches = [p async for p in (project_root / cache_root).glob('**/*.[yamljson]')]

    if not patches:
        return None

    logger.info('Load patches')
    return JsonPatch(
        [op for p in patches if p.suffix in ('yaml', 'yml', 'json') for op in await load_parse(p, cache, cache_root)]
    )


class TextLoader(abc.ABC):
    @abc.abstractmethod
    async def load(self, path: str) -> tuple[str, str]:
        """Return document text and its path, which could be URL path or local file path."""
        pass


class FileTextLoader(TextLoader):
    async def load(self, path: str) -> tuple[str, str]:
        return (await Path(path).read_text()), path


class HttpTextLoader(TextLoader):
    def __init__(self):
        self._client = httpx.AsyncClient()

    async def load(self, path: str) -> tuple[str, str]:
        response = await self._client.get(path)
        return response.text, response.url.path


async def get_document_text(path: str | Path) -> tuple[str, str]:
    match path:
        case str() if path.startswith(('http://', 'https://')):
            loader = HttpTextLoader()
        case Path():
            loader = FileTextLoader()
        case _:
            raise TypeError(type(path))

    return await loader.load(path)
