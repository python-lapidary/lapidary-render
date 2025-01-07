import logging
import sys
import typing
from collections.abc import AsyncIterator
from contextlib import contextmanager

import anyio
from jsonpatch import JsonPatch

from .config import Config

logger = logging.getLogger(__name__)


class ProcessorPlugin(typing.Protocol):
    async def process_mapping(self, model: dict, config: Config, project_root: anyio.Path) -> dict:
        pass


class JSONPatchPlugin(ProcessorPlugin):
    async def process_mapping(self, model: dict, config: Config, project_root: anyio.Path) -> dict:
        from jsonpointer import JsonPointerException

        async for path, patch in self.load_patches(project_root / 'openapi/patches'):
            logger.info('Applying patches from %s', path)
            try:
                model = patch.apply(model)
            except JsonPointerException as error:
                raise JsonPointerException(
                    f'Error while applying patch {str(path)}', error.args[0][:100] + '...'
                ) from None
        return model

    @staticmethod
    async def load_patches(patches_root: anyio.Path) -> AsyncIterator[tuple[anyio.Path, JsonPatch]]:
        from .load import load_parse

        patches = sorted([p async for p in patches_root.rglob('*[yamljson]')])

        if not patches:
            return

        logger.info('Load patches')

        for patch in patches:
            if patch.suffix in ('.yaml', '.yml', '.json'):
                path = patch.relative_to(patches_root)
                yield path, JsonPatch(await load_parse(patches_root, path))


@contextmanager
def sys_path_manager(path: str):
    """Context manager for temporarily adding a path to sys.path."""
    sys.path.append(path)
    try:
        yield
    finally:
        sys.path.remove(path)
