import sys
from pathlib import Path

import click


@click.group()
@click.version_option(package_name='lapidary.render', prog_name='lapidary')
@click.option('--verbose', is_flag=True, help='Enable debug logs.', default=False)
def app(verbose: bool) -> None:
    if verbose:
        import logging

        logging.basicConfig()
        logging.getLogger('lapidary').setLevel(logging.DEBUG)


@app.command()
@click.argument('document')
@click.argument('project_root', type=click.Path(path_type=Path, exists=False, file_okay=False, dir_okay=True))
@click.argument('package_name')
@click.option(
    '--save/--no-save',
    help="Copy the document in the project. The default is to save if it's a remote path",
    default=None,
)
def init(
    document: str,
    project_root: Path,
    package_name: str,
    save: bool | None,
):
    """Initialize a new project.

    DOCUMENT: Path or URL of the OpenAPI document

    PROJECT_ROOT: Root directory of the generated project

    PACKAGE_NAME: Root package for the generated code
    """

    from .main import init_project

    try:
        init_project(document, project_root, package_name, save)
    except FileExistsError:
        raise click.ClickException('Target exists')


@app.command()
@click.argument(
    'project_root', type=click.Path(path_type=Path, exists=True, file_okay=False, dir_okay=True), default='.'
)
def render(
    project_root: Path = Path(),
) -> None:
    """Generate Python code"""
    from .main import render_project

    render_project(project_root)


@app.command(hidden=True)
@click.argument(
    'project_root', type=click.Path(path_type=Path, exists=True, file_okay=False, dir_okay=True), default='.'
)
@click.option('--process', is_flag=True, help='Output processed python model', default=False)
def dump_model(
    project_root: Path = Path(),
    process: bool = False,
) -> None:
    from .main import dump_model as dump_model_

    dump_model_(project_root, process, sys.stdout)
