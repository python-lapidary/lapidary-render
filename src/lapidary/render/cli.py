import logging
from pathlib import Path
from typing import Annotated

import typer

from .config import Config
from .model import openapi, python
from .model.client_model import mk_client_model
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
def init(
    schema_path: Path,
    project_root: Path,
    package_name: str,
    patch: Annotated[
        list[Path],
        typer.Option(
            help="""A JSON Patch file or a directory of thereof. Can be used multiple times,
                     in which case only files are accepted.""",
        ),
    ] = None,
    format_strict: Annotated[bool, typer.Option(help=HELP_FORMAT_STRICT)] = False,
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
    patch: Annotated[
        list[Path],
        typer.Option(
            help="""A JSON Patch file or a directory of thereof. Can be used multiple times,
              in which case only files are accepted.""",
        ),
    ] = None,
):
    from pprint import pprint

    config = Config(
        package='package',
        format_strict=False,
        cache=False,
    )

    logger.info('Parse OpenAPI schema')
    oa_doc = load_spec(schema_path, patch, config)
    oa_model = openapi.OpenApiModel.model_validate(oa_doc)

    logger.info('Prepare model')
    model = mk_client_model(oa_model, python.ModulePath(config.package), get_resolver(oa_model, config.package))

    pprint(model)
