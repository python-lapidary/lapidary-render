import logging
from collections.abc import Callable, Iterable
from pathlib import Path, PurePath

import click
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


def update_project(
    modules: Iterable[python.AbstractModule],
    target_root: Path,
    root_package: str,
    update_progress: Callable[[python.AbstractModule], None],
):
    target_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    package_extras = PurePath(root_package) / 'extras'
    for module in modules:
        update_progress(module)
        cst_module = mk_module(module)
        if not cst_module:
            continue
        path = module.path.to_path()
        full_path = target_root / path.with_suffix('.py')
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(cst_module.code)
        written.append(full_path.relative_to(target_root))

    root_module_path = Path(root_package) / '__init__.py'
    (target_root / root_module_path).write_text(conv_cst.MODULE_ROOT.code)
    written.append(root_module_path)

    (target_root / root_package / 'py.typed').write_text('', newline='')
    written.append(Path(root_package, 'py.typed'))

    with click.progressbar(length=0, label='Removing stale files') as bar:
        for parent, dirs, files in target_root.walk(False):
            package = parent.relative_to(target_root)
            files_ = set(files)
            if package != package_extras:
                for existing in files:
                    path = (parent / existing).relative_to(target_root)

                    if path not in written:
                        bar.update(1, str(path))
                        files_.remove(existing)
                        (parent / existing).unlink()
            if not files_ and not dirs:
                bar.update(1, str(parent))
                parent.rmdir()


def write_gitignore(project_root: Path):
    (project_root / '.gitignore').write_text(
        """/dist/
__pycache__
"""
    )


def write_pyproject(project_root: Path, title: str, config: Config):
    import tomli_w

    from .pyproject import mk_pyproject_toml

    (project_root / 'pyproject.toml').write_text(
        f"""# This file was generated but won't be updated automatically and may be edited manually.

{tomli_w.dumps(mk_pyproject_toml(title, config))}"""
    )


def init_project(project_root: Path, config: Config, raw_document: dict):
    project_root.mkdir(parents=True, exist_ok=True)
    write_pyproject(project_root, raw_document['info']['title'], config)
    write_gitignore(project_root)
