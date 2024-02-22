import importlib.metadata
import logging
import pathlib

import anyio
import jinja2
import jinja2.loaders
from anyio import Path

from .config import Config, load_config
from .load import get_document_text, load_document
from .model import OpenApi30Converter, openapi, python

logger = logging.getLogger(__name__)
logging.getLogger('rybak').setLevel(logging.DEBUG)


async def init_project(
    project_root: Path,
    config: Config,
    save_document: bool,
) -> None:
    """Create project directory and pyproject file, download or copy the OpenAPI document"""

    if project_root.exists():
        raise Exception('Target exists')

    if save_document:
        config.document_path = copy_document(config, project_root)

    from rybak import render
    from rybak.jinja import JinjaAdapter

    environment = jinja2.Environment(
        loader=jinja2.loaders.PackageLoader('lapidary.render'),
    )
    excludes = [
        'includes',
        'gen',
    ]
    render(
        JinjaAdapter(environment),
        dict(
            get_version=importlib.metadata.version,
            config=config.model_dump(exclude_unset=True, exclude_defaults=True),
            document=await load_document(project_root, config, False),
        ),
        project_root,
        exclude_extend=excludes,
        remove_suffixes=['.jinja'],
    )


async def render(project_root: Path, cache: bool) -> None:
    model = await get_model(project_root, cache)

    logger.info('Render project')

    from rybak import render
    from rybak.jinja import JinjaAdapter

    environment = jinja2.Environment(
        loader=jinja2.loaders.PackageLoader('lapidary.render'),
    )
    excludes = [
        'includes',
        'pyproject.toml.jinja',
        'gen/{{model.package}}/auth.py.jinja',  # TODO auth
    ]
    render(
        JinjaAdapter(environment),
        dict(
            model=model,
            get_version=importlib.metadata.version,
        ),
        project_root,
        exclude_extend=excludes,
        remove_suffixes=['.jinja'],
    )


async def get_model(project_root: pathlib.Path, cache: bool) -> python.ClientModel:
    config = load_config(project_root)

    logger.info('Parse OpenAPI document')
    oa_doc = await load_document(anyio.Path(project_root), config, cache)

    oa_model = openapi.OpenApiModel.model_validate(oa_doc)

    logger.info('Prepare python model')
    return OpenApi30Converter(python.ModulePath(config.package), oa_model).process()


async def copy_document(config: Config, project_root: Path) -> Path:
    document_text, path = get_document_text(config.document_path)

    target = project_root / 'src' / 'openapi' / Path(path).name
    await target.parent.mkdir(parents=True)
    await target.write_text(document_text)
    return target.relative_to(project_root)
