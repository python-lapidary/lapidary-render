import logging
from collections.abc import Callable, Iterable
from pathlib import PurePath

import anyio
import asyncclick
import libcst as cst

from .config import Config
from .model import conv_cst, python

logger = logging.getLogger(__name__)


def mk_module(module: python.AbstractModule) -> cst.Module | None:
    match module:
        case python.SchemaModule():
            return conv_cst.mk_schema_module(module)
        case python.ClientModule():
            return conv_cst.mk_client_module(module)
        case python.SecurityModule():
            if not module.body:
                return None
            return conv_cst.mk_security_module(module)
        case python.MetadataModule():
            return conv_cst.mk_metadata_module(module)
        case python.EmptyModule():
            return conv_cst.MODULE_EMPTY
        case _:
            raise TypeError(type(module))


async def update_project(
    modules: Iterable[python.AbstractModule],
    target_root: anyio.Path,
    root_package: str,
    update_progress: Callable[[python.AbstractModule], None],
):
    await target_root.mkdir(parents=True, exist_ok=True)
    written: list[anyio.Path] = []
    package_extras = PurePath(root_package) / 'extras'
    for module in modules:
        update_progress(module)
        cst_module = mk_module(module)
        if not cst_module:
            continue
        path = module.path.to_path()
        full_path = target_root / path.with_suffix('.py')
        await full_path.parent.mkdir(parents=True, exist_ok=True)
        await full_path.write_text(cst_module.code)
        written.append(full_path.relative_to(target_root))

    root_module_path = anyio.Path(root_package) / '__init__.py'
    await (target_root / root_module_path).write_text(conv_cst.MODULE_ROOT.code)
    written.append(root_module_path)

    await (target_root / root_package / 'py.typed').write_text('', newline='')
    written.append(anyio.Path(root_package, 'py.typed'))

    with asyncclick.progressbar(length=0, label='Removing stale files') as bar:
        async for parent, dirs, files in target_root.walk(False):
            package = parent.relative_to(target_root)
            files_ = set(files)
            if package != package_extras:
                for existing in files:
                    path = (parent / existing).relative_to(target_root)

                    if path not in written:
                        bar.update(1, str(path))
                        files_.remove(existing)
                        await (parent / existing).unlink()
            if not files_ and not dirs:
                bar.update(1, str(parent))
                await parent.rmdir()


GITIGNORE_LINES = (
    '/dist/',
    '__pycache__',
)


async def write_gitignore(project_root: anyio.Path):
    async with await anyio.open_file(project_root / '.gitignore', 'w') as f:
        await f.writelines(GITIGNORE_LINES)


async def write_pyproject(project_root: anyio.Path, title: str, config: Config):
    import tomli_w

    from .pyproject import mk_pyproject_toml

    await (project_root / 'pyproject.toml').write_text(
        f"""# This file was generated but won't be updated automatically and may be edited manually.

{tomli_w.dumps(mk_pyproject_toml(title, config))}
"""
    )


async def init_project(project_root: anyio.Path, config: Config, raw_document: dict):
    await project_root.mkdir(parents=True, exist_ok=True)
    await write_pyproject(project_root, raw_document['info']['title'], config)
    await write_gitignore(project_root)
