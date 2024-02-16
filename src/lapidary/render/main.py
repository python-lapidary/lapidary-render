import importlib.metadata
import logging
import os
import shutil
from collections.abc import Collection
from pathlib import Path

import jinja2
import jinja2.loaders
import yaml
from rybak.jinja import JinjaAdapter

from .config import Config
from .model import openapi, python
from .model.openapi_conv import OpenApi30Converter
from .spec import load_spec

logger = logging.getLogger(__name__)
logging.getLogger('rybak').setLevel(logging.DEBUG)


def init_project(
    schema_path: Path,
    project_root: Path,
    config: Config,
    render: bool,
    patches: Collection[Path],
):
    # (project_root / config.openapi_root).mkdir(parents=True)
    # package_path = project_root / config.gen_root / config.package
    # package_path.mkdir(parents=True)
    #
    # copy_schema(config, project_root, schema_path)
    # if patches:
    #     copy_patches(config, project_root, patches)

    logger.info('Parse OpenAPI schema')
    oa_doc = load_spec(schema_path, patches, config)

    excludes = ['includes', 'gen/{{model.package}}/auth.py.jinja']
    if not render:
        logger.info('Skip rendering client.')
        excludes.append('gen')

    oa_model = openapi.OpenApiModel.model_validate(oa_doc)

    logger.info('Prepare model')

    from rybak import render

    model = OpenApi30Converter(python.ModulePath(config.package), oa_model).process()

    logger.info('Render project')
    environment = jinja2.Environment(
        loader=jinja2.loaders.PackageLoader('lapidary.render'),
    )
    environment.globals.update(
        dict(
            as_module_path=python.ModulePath,
            os=os,
        )
    )
    environment.filters.update(dict(toyaml=yaml.safe_dump))
    render(
        JinjaAdapter(environment),
        dict(
            model=model,
            document=oa_doc,
            get_version=importlib.metadata.version,
            auth_module=None,
        ),
        project_root,
        exclude_extend=excludes,
        remove_suffixes=['.jinja'],
    )


def copy_schema(config: Config, project_root: Path, schema_path: Path):
    logger.info('Copy OpenAPI schema to %s', config.get_openapi(project_root))
    shutil.copyfile(schema_path, config.get_openapi(project_root))


def copy_patches(config: Config, project_root: Path, patches: Collection[Path]) -> None:
    patches_dir = config.get_patches(project_root)
    logger.info('Copy patches to %s', patches_dir)
    assert patches

    if len(patches) > 1:
        if not all(path.is_file() for path in patches):
            raise ValueError('When passing multiple patch paths, all must be files')

        patches_dir.mkdir()

        for file in patches:
            shutil.copyfile(file, patches_dir / file.name)

    else:
        shutil.copytree(next(iter(patches)), patches_dir)
