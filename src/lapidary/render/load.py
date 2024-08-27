import abc
import importlib.machinery
import importlib.util
import logging
from collections.abc import Mapping, MutableSequence, Sequence
from typing import cast

import anyio
import httpx
import ruamel.yaml

from .config import Config
from .plugins import ProcessorPlugin, sys_path_manager

logger = logging.getLogger(__name__)


async def load_document(root: anyio.Path, config: Config) -> Mapping:
    logger.info('Load OpenAPI document')
    spec_dict: dict = cast(dict, await load_parse(root, config.document_path))

    if config.plugins:
        spec_dict = await apply_processor_plugins(spec_dict, config, root)

    return spec_dict


async def apply_processor_plugins(descr_dict: dict, config: Config, project_root: anyio.Path) -> dict:
    processor_classes: MutableSequence[type[ProcessorPlugin]] = []
    with sys_path_manager(str(project_root / 'plugins')):
        for plugin_path in config.plugins:
            module_name, class_name = plugin_path.split(':')
            processor_classes.append(getattr(importlib.import_module(module_name), class_name))

    for factory in processor_classes:
        processor = factory()
        descr_dict = await processor.process_mapping(descr_dict, config, project_root)

    return descr_dict


async def load_parse(root: anyio.Path, path: str | anyio.Path) -> Mapping | Sequence:
    text = await document_handler_for(root, path).load()
    return parse(text)


def parse(text: str) -> Mapping:
    yaml = ruamel.yaml.YAML(typ='safe')
    return yaml.load(text)


class DocumentHandler[P: str | anyio.Path](abc.ABC):
    def __init__(self, path: P) -> None:
        self._path = path

    @abc.abstractmethod
    async def load(self) -> str:
        """Return document text and, which could be URL path or local file path."""

    @property
    @abc.abstractmethod
    def is_url(self) -> bool:
        pass

    @property
    def path(self) -> str:
        return str(self._path)

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

    @property
    def is_url(self) -> bool:
        return False


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
        _, name = split(parsed.path)
        return name

    async def save_to(self, target: anyio.Path) -> str:
        text = await self.load()
        file_name = self._file_name()
        await (target / file_name).write_text(text)
        return file_name

    @property
    def is_url(self) -> bool:
        return True


def document_handler_for(document_root: anyio.Path, path: str | anyio.Path) -> DocumentHandler:
    match path:
        case str() if path.startswith(('http://', 'https://')):
            return HttpDocumentHandler(path)
        case _:
            return FileDocumentHandler(document_root, anyio.Path(path))
