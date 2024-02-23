import logging
from pathlib import Path
from typing import Annotated

import anyio
import typer

from .config import Config
from .main import get_model, init_project
from .main import render as render_

HELP_FORMAT_STRICT = 'Use black in slow (strict checking) mode'

logging.basicConfig()
logging.getLogger('lapidary').setLevel(logging.DEBUG)
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
    document: Annotated[str, typer.Argument(help='Path of URL of the OpenAPI document.')],
    project_root: Annotated[Path, typer.Argument(help='Root directory of the generated project')],
    package_name: Annotated[str, typer.Argument(help='Root package for the generated code.')],
    cache: Annotated[bool, typer.Option(help='Save parsed document as a pickle file.')] = False,
    save: Annotated[bool, typer.Option(help='Copy the document in the project.')] = False,
):
    """Create a new project."""

    config = Config(
        package=package_name,
        document_path=document,
        cache=cache,
    )

    anyio.run(init_project, project_root, config, save)


@app.command()
def render(
    project_root: Annotated[Path, typer.Argument()] = Path(),
    cache: bool = False,
) -> None:
    anyio.run(render_, project_root, cache)


@app.command()
def dump_model(
    project_root: Annotated[Path, typer.Argument()] = Path(),
):
    from pprint import pprint

    model = anyio.run(get_model, project_root, False)
    pprint(model)
