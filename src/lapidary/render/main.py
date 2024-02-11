import importlib.metadata
import logging
import os
import shutil
from collections.abc import Collection
from hashlib import sha3_256
from pathlib import Path

import jinja2
import jinja2.loaders
import yaml
from rybak.jinja import JinjaAdapter

from .client import mk_model
from .config import Config
from .model import openapi, python
from .model.auth_module import get_auth_module
from .model.client_model import mk_client_model
from .model.refs import get_resolver
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

    excludes = [
        'includes',
    ]
    if not render:
        logger.info('Skip rendering client.')
        excludes.append('gen')

    oa_model = openapi.OpenApiModel.model_validate(oa_doc)

    logger.info('Prepare model')

    from rybak import render

    model = mk_client_model(oa_model, python.ModulePath(config.package), get_resolver(oa_model, config.package))

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
            auth_module=get_auth_module(oa_model, python.ModulePath(config.package) / 'auth'),
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


def update_project(project_root: Path, config: Config) -> None:
    from .spec import load_spec

    oa_doc = load_spec(project_root, config)

    from . import jinja

    jinja.model = openapi.OpenApiModel.parse_obj(oa_doc)
    jinja.document = oa_doc
    jinja.package = config.package

    from copier import run_update

    run_update(
        str(project_root),
        mk_model(jinja.model, config, calculate_signture(oa_doc)),
        exclude=(
            'pyproject.toml',
            'includes',
        ),
        vcs_ref='HEAD',
        defaults=True,
        overwrite=True,
    )


def calculate_signture(doc: dict) -> str:
    return sha3_256(yaml.safe_dump(doc).encode()).hexdigest()
