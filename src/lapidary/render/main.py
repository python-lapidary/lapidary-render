import logging
import shutil
from hashlib import sha3_256
from pathlib import Path

import yaml
from lapidary.runtime import openapi

from .client import mk_model
from .config import Config

logger = logging.getLogger(__name__)


def init_project(
        schema_path: Path,
        project_root: Path,
        config: Config,
        render: bool,
):
    (project_root / config.openapi_root).mkdir(parents=True)
    package_path = project_root / config.gen_root / config.package
    package_path.mkdir(parents=True)

    copy_pyproj(config, project_root, schema_path)
    text = config.get_openapi(project_root).read_text()
    oa_doc = yaml.safe_load(text)

    excludes = ['includes']
    if not render:
        logger.info('Skip rendering client.')
        excludes.extend(("gen",))

    from . import jinja
    jinja.model = openapi.OpenApiModel.parse_obj(oa_doc)
    jinja.document = oa_doc
    jinja.package = config.package

    from copier import run_copy

    run_copy(
        "/Users/matte/Documents/Projects/lapidary-template",
        str(project_root),
        mk_model(jinja.model, config, calculate_signture(oa_doc)),
        exclude=excludes,
        skip_if_exists=[
            "pyproject.toml"
        ],
        vcs_ref="HEAD",
        defaults=True,
    )


def copy_pyproj(config, project_root, schema_path):
    logger.info('Copy OpenAPI schema to %s', config.get_openapi(project_root))
    shutil.copyfile(schema_path, config.get_openapi(project_root))


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
