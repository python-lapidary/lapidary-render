import logging
import sys
from pathlib import Path

import anyio
import asyncclick as click

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(package_name='lapidary.render', prog_name='lapidary')
def app() -> None:
    pass


@app.command()
@click.argument('document')
@click.argument('project_root')
@click.argument('package_name')
@click.option('--save/--no-save', help='Copy the document in the project', default=False)
async def init(
    document: str,
    project_root: str,
    package_name: str,
    save: bool = False,
):
    """Initialize a new project.

    DOCUMENT: Path or URL of the OpenAPI document

    PROJECT_ROOT: Root directory of the generated project

    PACKAGE_NAME: Root package for the generated code
    """

    from .main import init_project

    try:
        await init_project(document, anyio.Path(project_root), package_name, save)
    except FileExistsError:
        raise click.ClickException('Target exists')


@app.command()
@click.argument('project_root', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.')
async def render(
    project_root: Path = Path(),
) -> None:
    """Generate Python code"""
    from .main import render_project

    await render_project(anyio.Path(project_root))


@app.command(hidden=True)
@click.argument('project_root', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.')
@click.option('--process', is_flag=True, help='Output processed python model', default=False)
async def dump_model(
    project_root: Path = Path(),
    process: bool = False,
) -> None:
    from .main import dump_model as dump_model_

    await dump_model_(anyio.Path(project_root), process, sys.stdout)
