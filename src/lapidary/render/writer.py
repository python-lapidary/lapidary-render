import logging
import shutil
from collections.abc import Callable, Iterable

import anyio
import asyncclick

from .model import conv_cst, python

logger = logging.getLogger(__name__)


async def write_all(
    modules: Iterable[python.AbstractModule],
    src_root: anyio.Path | None,
    target_root: anyio.Path,
    root_package: str,
    update_progress: Callable[[python.AbstractModule], None],
):
    await target_root.mkdir(parents=True, exist_ok=True)
    written: list[anyio.Path] = []
    for module in modules:
        update_progress(module)
        path = module.path.to_path()
        full_path = target_root / path.with_suffix('.py')
        match module:
            case python.SchemaModule():
                code = conv_cst.mk_schema_module(module).code
            case python.ClientModule():
                code = conv_cst.mk_client_module(module).code
            case python.SecurityModule():
                if not module.body:
                    continue
                code = conv_cst.mk_security_module(module).code
            case python.MetadataModule():
                code = conv_cst.mk_metadata_module(module).code
            case python.EmptyModule():
                code = conv_cst.MODULE_EMPTY.code
            case _:
                raise TypeError(type(module))
        await full_path.parent.mkdir(parents=True, exist_ok=True)
        await full_path.write_text(code)
        written.append(full_path.relative_to(target_root))

    root_module_path = anyio.Path(root_package) / '__init__.py'
    await (target_root / root_module_path).write_text(conv_cst.MODULE_ROOT.code)
    written.append(root_module_path)

    await (target_root / root_package / 'py.typed').write_text('', newline='')
    written.append(anyio.Path(root_package, 'py.typed'))

    if src_root:
        with asyncclick.progressbar(length=0, label='Copying extra sources') as bar:
            async for parent, _, files in src_root.walk():
                bar.length += len(files)
                target_parent = target_root / parent.relative_to(src_root)
                await target_parent.mkdir(parents=True, exist_ok=True)
                for file in files:
                    rel_path = parent.relative_to(src_root) / file
                    bar.update(1, str(rel_path))
                    shutil.copy(parent / file, target_root / file)
                    written.append(rel_path)

    with asyncclick.progressbar(length=0, label='Removing stale files') as bar:
        async for parent, dirs, files in target_root.walk(False):
            files_ = set(files)
            for existing in files:
                path = (parent / existing).relative_to(target_root)

                if path not in written:
                    bar.update(1, str(path))
                    files_.remove(existing)
                    await (parent / existing).unlink()
            if not files_ and not dirs:
                bar.update(1, str(parent))
                await parent.rmdir()
