import importlib.metadata
import logging
import pathlib
from typing import TextIO

import anyio
import jinja2
import jinja2.loaders
import ruamel.yaml

from .config import Config, load_config
from .load import document_handler_for, load_document
from .model import OpenApi30Converter, openapi, python

logger = logging.getLogger(__name__)
logging.getLogger('rybak').setLevel(logging.DEBUG)


async def init_project(
    project_root: anyio.Path,
    config: Config,
    save_document: bool,
) -> None:
    """Create project directory and pyproject file, download or copy the OpenAPI document"""

    if await project_root.exists():
        raise FileExistsError

    document_handler = document_handler_for(anyio.Path(), config.document_path)

    if save_document:
        document_root = anyio.Path('src/openapi')
        target_dir = project_root / document_root
        await target_dir.mkdir(parents=True)
        file_name = await document_handler.save_to(target_dir)
        config.document_path = document_root / file_name

    yaml = ruamel.yaml.YAML(typ='safe')
    document = yaml.load(await document_handler.load())

    from rybak import TreeTemplate
    from rybak.jinja import JinjaAdapter

    TreeTemplate(
        JinjaAdapter(
            jinja2.Environment(
                loader=jinja2.loaders.PackageLoader('lapidary.render'),
            )
        ),
        exclude_extend=[
            'includes',
            'gen',
        ],
        remove_suffixes=['.jinja'],
    ).render(
        dict(
            get_version=importlib.metadata.version,
            config=config.model_dump(exclude_unset=True, exclude_defaults=True),
            document=document,
        ),
        pathlib.Path(project_root),
    )


async def render_project(project_root: anyio.Path, cache: bool) -> None:
    config = await load_config(project_root)

    logger.info('Parse OpenAPI document')
    oa_doc = await load_document(project_root, config, cache)
    oa_model = openapi.OpenApiModel.model_validate(oa_doc)

    logger.info('Prepare python model')
    model = OpenApi30Converter(python.ModulePath(config.package), oa_model).process()

    logger.info('Render project')

    from rybak import TreeTemplate
    from rybak.jinja import JinjaAdapter

    TreeTemplate(
        JinjaAdapter(
            jinja2.Environment(
                loader=jinja2.loaders.PackageLoader('lapidary.render'),
            )
        ),
        exclude_extend=[
            'includes',
            'pyproject.toml.jinja',
            'gen/{{model.package}}/auth.py.jinja',  # TODO auth
        ],
        remove_suffixes=['.jinja'],
    ).render(
        dict(
            model=model,
            get_version=importlib.metadata.version,
        ),
        pathlib.Path(project_root),
    )


async def dump_model(project_root: anyio.Path, process: bool, output: TextIO):
    from pprint import pprint

    config = await load_config(project_root)
    oa_doc = await load_document(project_root, config, False)

    if not process:
        yaml = ruamel.yaml.YAML(typ='safe')
        yaml.dump(oa_doc, output)

    else:
        oa_model = openapi.OpenApiModel.model_validate(oa_doc)
        py_model = OpenApi30Converter(python.ModulePath(config.package), oa_model).process()
        pprint(py_model, output)
