from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path, PurePath
from typing import TextIO

import click
import pydantic

from .config import Config, load_config
from .load import document_handler_for, load_document
from .model import python
from .yaml import yaml

logger = logging.getLogger(__name__)


def init_project(
    document_path: str,
    project_root: Path,
    package_name: str,
    save_document: bool | None,
) -> None:
    """Create project directory and pyproject file, download or copy the OpenAPI document"""

    if project_root.exists():
        raise FileExistsError

    from .writer import init_project

    document_handler = document_handler_for(Path(), document_path)

    if save_document is None and document_handler.is_url:
        # default is save if document is remote
        save_document = True

    if save_document:
        document_root = Path('lapidary/openapi')
        target_dir = project_root / document_root
        target_dir.mkdir(parents=True)
        file_name = document_handler.save_to(target_dir)
        config_document_path = str(document_root / file_name)
    else:
        logger.warning('Saving OpenAPI document is recommended for portable and repeatable builds')
        if not document_handler.is_url:
            document_path_path = PurePath(document_path)
            if not document_path_path.is_absolute():
                # document path is a file outside of the project root.
                # If it's relative, make it relative to the project root.
                try:
                    config_document_path = str(document_path_path.relative_to(project_root, walk_up=True))
                except ValueError:
                    config_document_path = str(Path.cwd() / document_path_path)
            else:
                config_document_path = document_path
        else:
            config_document_path = document_path

    config = Config(
        # if path is not URL and not saving the file
        document_path=config_document_path,
        origin=document_handler.path if document_handler.is_url else None,
        package=package_name,
    )

    document = yaml.load(document_handler.load())

    init_project(project_root, config, document)


def render_project(project_root: Path) -> None:
    from .writer import update_project

    config = load_config(project_root)

    logger.info('Parse OpenAPI document')
    oa_doc = load_document(project_root, config)
    model = prepare_python_model(oa_doc, config)

    logger.info('Render project')
    with click.progressbar(
        model.modules,
        label='Rendering modules',
        item_show_func=lambda module: str(module.path) if module else '',
        show_pos=True,
    ) as progressbar:

        def progress(module: python.AbstractModule) -> None:
            progressbar.update(1, module)

        update_project(
            model.modules,
            project_root / 'src',
            config.package,
            progress,
        )


def dump_model(project_root: Path, process: bool, output: TextIO):
    config = load_config(project_root)
    oa_doc = load_document(project_root, config)

    if not process:
        yaml.dump(oa_doc, output)

    else:
        py_model = prepare_python_model(oa_doc, config)
        doc = pydantic.TypeAdapter(python.ClientModel).dump_python(py_model, mode='json', exclude_none=True)
        yaml.dump(doc, output)


def prepare_python_model(oa_doc: Mapping, config: Config) -> python.ClientModel:
    from .model import conv_openapi, openapi

    oa_model = openapi.OpenAPI.model_validate(oa_doc)
    with click.progressbar(
        length=len(oa_model.paths.paths),
        label='Processing paths',
        item_show_func=str,
        show_pos=True,
    ) as pbar:
        logger.info('Prepare python model')
        return conv_openapi.OpenApi30Converter(
            python.ModulePath(config.package),
            oa_model,
            str(config.origin) if config.origin else None,
            path_progress=lambda item: pbar.update(1, item),
        ).process()
