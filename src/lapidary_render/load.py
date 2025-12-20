import abc
import logging
from collections.abc import Mapping
from pathlib import Path

import httpx

from .config import Config

logger = logging.getLogger(__name__)


def load_document(root: Path, config: Config) -> Mapping:
    from .yaml import yaml

    logger.info('Load OpenAPI document')

    text = document_handler_for(root, config.document_path).load()
    return yaml.load(text)


class DocumentHandler(abc.ABC):
    def __init__(self, path: str) -> None:
        self._path = path

    @abc.abstractmethod
    def load(self) -> str:
        """Return document text and, which could be URL path or local file path."""

    @property
    @abc.abstractmethod
    def is_url(self) -> bool:
        pass

    @property
    def path(self) -> str:
        return str(self._path)

    @abc.abstractmethod
    def save_to(self, target: Path) -> str:
        """Save the document.
        :param target: target directory
        :return: file name of the saved document"""


class FileDocumentHandler(DocumentHandler):
    def __init__(self, project_root: Path, path: str) -> None:
        assert isinstance(project_root, Path)
        super().__init__(path)
        self._project_root = project_root

    def load(self) -> str:
        return (self._project_root / self._path).read_text()

    def save_to(self, target: Path) -> str:
        import shutil

        src_path = Path(self._path)
        shutil.copyfile(self._path, target / src_path.name)
        return src_path.name

    @property
    def is_url(self) -> bool:
        return False


class HttpDocumentHandler(DocumentHandler):
    def __init__(self, path: str) -> None:
        super().__init__(path)
        self._client = httpx.Client(timeout=30.0)
        self._cache: str | None = None

    def load(self) -> str:
        if not self._cache:
            response = self._client.get(self._path)
            self._cache = response.text
        assert self._cache is not None
        return self._cache

    def _file_name(self) -> str:
        from os.path import split
        from urllib.parse import urlparse

        parsed = urlparse(self._path)
        _, name = split(parsed.path)
        return name or 'openapi.yaml'

    def save_to(self, target: Path) -> str:
        text = self.load()
        file_name = self._file_name()
        (target / file_name).write_text(text)
        return file_name

    @property
    def is_url(self) -> bool:
        return True


def document_handler_for(document_root: Path, path: str) -> DocumentHandler:
    if path.startswith(('http://', 'https://')):
        return HttpDocumentHandler(path)
    else:
        return FileDocumentHandler(document_root, str(path))
