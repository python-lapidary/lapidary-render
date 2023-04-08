import logging
import shutil
from collections.abc import Collection
from hashlib import sha3_256
from pathlib import Path

import yaml
from lapidary.runtime import openapi

from .client import mk_model
from .config import Config
from .spec import load_spec

logger = logging.getLogger(__name__)


def init_project(
        schema_path: Path,
        project_root: Path,
        config: Config,
        render: bool,
        patches: Collection[Path],
):
    (project_root / config.openapi_root).mkdir(parents=True)
    package_path = project_root / config.gen_root / config.package
    package_path.mkdir(parents=True)

    copy_schema(config, project_root, schema_path)
    if patches:
        copy_patches(config, project_root, patches)

    logger.info("Parse OpenAPI schema")
    oa_doc = load_spec(project_root, config)

    excludes = ['includes']
    if not render:
        logger.info('Skip rendering client.')
        excludes.extend(("gen",))

    from . import jinja
    jinja.model = openapi.OpenApiModel.parse_obj(oa_doc)
    jinja.document = oa_doc
    jinja.package = config.package

    from copier import run_copy

    logger.info("Pre-process model")
    render_model = mk_model(jinja.model, config, calculate_signture(oa_doc))

    logger.info("Render project")
    run_copy(
        "/Users/matte/Documents/Projects/lapidary-template",
        str(project_root),
        render_model,
        exclude=excludes,
        vcs_ref="HEAD",
        defaults=True,
    )


def copy_schema(config: Config, project_root: Path, schema_path: Path):
    logger.info('Copy OpenAPI schema to %s', config.get_openapi(project_root))
    shutil.copyfile(schema_path, config.get_openapi(project_root))


def copy_patches(config: Config, project_root: Path, patches: Collection[Path]) -> None:
    patches_dir = config.get_patches(project_root)
    logger.info("Copy patches to %s", patches_dir)
    assert patches

    if len(patches) > 1:
        if not all((path.is_file() for path in patches)):
            raise ValueError("When passing multiple patch paths, all must be files")

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
        vcs_ref="HEAD",
        defaults=True,
        overwrite=True,
    )


def calculate_signture(doc: dict) -> str:
    return sha3_256(yaml.safe_dump(doc).encode()).hexdigest()
