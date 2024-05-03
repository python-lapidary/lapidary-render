import logging
import sys
from pathlib import Path
from typing import Annotated

import anyio
import typer

from .config import Config

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

    from .main import init_project

    config = Config(
        package=package_name,
        document_path=document,
        cache=cache,
    )

    try:
        anyio.run(init_project, anyio.Path(project_root), config, save)
    except FileExistsError:
        print('Target exists')
        raise typer.Exit(-1)


@app.command()
def render(
    project_root: Annotated[Path, typer.Argument()] = Path(),
    cache: bool = False,
) -> None:
    from .main import render_project

    anyio.run(render_project, anyio.Path(project_root), cache)


@app.command()
def dump_model(
    project_root: Annotated[Path, typer.Argument()] = Path(),
    process: Annotated[bool, typer.Option(help='Output processed python model')] = False,
) -> None:
    from .main import dump_model as dump_model_

    anyio.run(dump_model_, anyio.Path(project_root), process, sys.stdout)
