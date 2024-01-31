import logging
from pathlib import Path

import typer

from .config import Config, load_config
from .model.client_model import mk_client_model
from .model.python.module_path import ModulePath
from .model.refs import get_resolver
from .spec import load_spec

HELP_FORMAT_STRICT = 'Use black in slow (strict checking) mode'

logging.basicConfig()
logging.getLogger('lapidary').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def version():
    """Print version and exit."""

    from importlib.metadata import version
    package = 'lapidary'
    print(f'{package}, {version(package)}')


@app.command()
def update(
        project_root: Path = typer.Argument(Path('')),
        format_strict: bool = typer.Option(False, help=HELP_FORMAT_STRICT),
        cache: bool = True
):
    """Update existing project. Read configuration from pyproject.yaml ."""

    if not project_root.exists():
        logger.error(f"'Target '{project_root}' doesn't exists'")
        raise typer.Exit(code=1)

    from .main import update_project

    try:
        config = load_config(project_root)
    except (KeyError, FileNotFoundError):
        raise SystemExit('Missing Lapidary configuration')

    config.format_strict = format_strict
    config.cache = cache
    update_project(project_root, config)


@app.command()
def init(
        schema_path: Path,
        project_root: Path,
        package_name: str,
        patch: list[Path] = typer.Option(
            None,
            help="""A JSON Patch file or a directory of thereof. Can be used multiple times,
                     in which case only files are accepted."""),
        format_strict: bool = typer.Option(False, help=HELP_FORMAT_STRICT),
        render: bool = True,
        cache: bool = True,
):
    """Create a new project from scratch."""

    if project_root.exists():
        logger.error(f'Target "{project_root}" exists')
        raise typer.Exit(code=1)

    from .main import init_project

    config = Config(
        package=package_name,
        format_strict=format_strict,
        cache=cache,
    )

    init_project(schema_path, project_root, config, render, patch)


@app.command()
def dump_model(
        schema_path: Path,
        patch: list[Path] = typer.Option(
            None,
            help="""A JSON Patch file or a directory of thereof. Can be used multiple times,
              in which case only files are accepted."""),
):
    config = Config(
        package='package',
        format_strict=False,
        cache=False,
    )

    logger.info("Parse OpenAPI schema")
    oa_doc = load_spec(schema_path, patch, config)
    from lapidary.render.model import openapi
    oa_model = openapi.OpenApiModel.model_validate(oa_doc)

    logger.info("Prepare model")
    model = mk_client_model(oa_model, ModulePath(config.package), get_resolver(oa_model, config.package))

    from pprint import pprint
    pprint(model)
