import abc
import hashlib
import logging
import pickle
from collections.abc import Iterable, Mapping, Sequence
from typing import cast

import anyio
import httpx
import platformdirs
import ruamel.yaml
from jsonpatch import JsonPatch

from .config import Config

logger = logging.getLogger(__name__)


async def load_document(root: anyio.Path, config: Config, cache: bool) -> Mapping:
    cache_root = anyio.Path(platformdirs.user_cache_path('lapidary'))

    logger.info('Load OpenAPI document')
    spec_dict: dict = cast(dict, await load_parse(root, config.document_path, cache, cache_root))

    if (patch := await load_patches(root / config.patches, cache, cache_root)) is not None:
        spec_dict = patch.apply(spec_dict)

    return spec_dict


async def load_parse(
    root: anyio.Path, path: str | anyio.Path, cache: bool, cache_root: anyio.Path
) -> Mapping | Sequence:
    text = await document_handler_for(root, path).load()
    if cache:
        return await parse_cache(text, cache_root)
    else:
        return parse(text)


async def parse_cache(text: str, cache_root: anyio.Path) -> Mapping:
    digest = hashlib.sha224(text.encode()).hexdigest()
    cache_path = anyio.Path((cache_root / digest).with_suffix('.pickle' + str(pickle.HIGHEST_PROTOCOL)))
    if await cache_path.exists():
        b = await cache_path.read_bytes()
        return pickle.loads(b)
    else:
        d = parse(text)
        await cache_root.mkdir(parents=True, exist_ok=True)
        await cache_path.write_bytes(pickle.dumps(d, pickle.HIGHEST_PROTOCOL))
        return d


def parse(text: str) -> Mapping:
    yaml = ruamel.yaml.YAML(typ='safe')
    return yaml.load(text)


async def load_patches(patches_root: anyio.Path, cache: bool, cache_root: anyio.Path) -> JsonPatch | None:
    patches = [p async for p in patches_root.rglob('*[yamljson]')]

    if not patches:
        return None

    logger.info('Load patches')
    return JsonPatch(
        [
            op
            for p in patches
            if p.suffix in ('.yaml', '.yml', '.json')
            for op in cast(Iterable, await load_parse(patches_root, p.relative_to(patches_root), cache, cache_root))
        ]
    )


class DocumentHandler[P: str | anyio.Path](abc.ABC):
    def __init__(self, path: P) -> None:
        self._path = path

    @abc.abstractmethod
    async def load(self) -> str:
        """Return document text and its path, which could be URL path or local file path."""

    @abc.abstractmethod
    async def save_to(self, target: anyio.Path) -> str:
        """Save the document.
        :param target: target directory
        :return: file name of the saved document"""


class FileDocumentHandler(DocumentHandler[anyio.Path]):
    def __init__(self, project_root: anyio.Path, path: anyio.Path) -> None:
        assert isinstance(project_root, anyio.Path)
        assert isinstance(path, anyio.Path)
        super().__init__(path)
        self._project_root = project_root

    async def load(self) -> str:
        return await (self._project_root / self._path).read_text()

    async def save_to(self, target: anyio.Path) -> str:
        import shutil

        shutil.copyfile(self._path, target / self._path.name)
        return self._path.name


class HttpDocumentHandler(DocumentHandler[str]):
    def __init__(self, path: str) -> None:
        super().__init__(path)
        self._client = httpx.AsyncClient()
        self._cache: str | None = None

    async def load(self) -> str:
        if not self._cache:
            response = await self._client.get(self._path)
            self._cache = response.text
        assert self._cache is not None
        return self._cache

    def _file_name(self) -> str:
        from os.path import split
        from urllib.parse import urlparse

        parsed = urlparse(self._path)
        name, _ = split(parsed.path)
        return name

    async def save_to(self, target: anyio.Path) -> str:
        text = await self.load()
        file_name = self._file_name()
        await (target / file_name).write_text(text)
        return file_name


def document_handler_for(document_root: anyio.Path, path: str | anyio.Path) -> DocumentHandler:
    match path:
        case str() if path.startswith(('http://', 'https://')):
            return HttpDocumentHandler(path)
        case _:
            return FileDocumentHandler(document_root, anyio.Path(path))
