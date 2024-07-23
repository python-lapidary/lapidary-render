import importlib.metadata
import logging
import pathlib
from collections.abc import Mapping
from typing import Any, TextIO

import anyio
import asyncclick as click
import jinja2
import jinja2.loaders
import ruamel.yaml
import rybak

from .config import Config, load_config
from .load import document_handler_for, load_document
from .model import OpenApi30Converter, openapi, python

logger = logging.getLogger(__name__)


async def init_project(
    document_path: str,
    project_root: anyio.Path,
    package_name: str,
    save_document: bool,
) -> None:
    """Create project directory and pyproject file, download or copy the OpenAPI document"""

    if await project_root.exists():
        raise FileExistsError

    document_handler = document_handler_for(anyio.Path(), document_path)

    if save_document:
        document_root = anyio.Path('src/openapi')
        target_dir = project_root / document_root
        await target_dir.mkdir(parents=True)
        file_name = await document_handler.save_to(target_dir)
        config_document_path = str(document_root / file_name)
    else:
        logger.warning('Saving OpenAPI document is recommended for portable and repeatable builds')
        if not document_handler.is_url:
            document_path_path = pathlib.PurePath(document_path)
            if not document_path_path.is_absolute():
                # document path is a file outside of the project root.
                # If it's relative, make it relative to the project root.
                try:
                    config_document_path = str(document_path_path.relative_to(project_root, walk_up=True))
                except ValueError:
                    config_document_path = str(await anyio.Path.cwd() / document_path_path)
            else:
                config_document_path = document_path
        else:
            config_document_path = None

    config = Config(
        # if path is not URL and not saving the file
        document_path=config_document_path,
        origin=document_handler.path if document_handler.is_url else None,
        package=package_name,
    )

    yaml = ruamel.yaml.YAML(typ='safe')
    document = yaml.load(await document_handler.load())

    from rybak import TreeTemplate
    from rybak.jinja import JinjaAdapter

    TreeTemplate(
        JinjaAdapter(
            jinja2.Environment(
                loader=jinja2.loaders.PackageLoader('lapidary.render', package_path='templates/init'),
            )
        ),
        remove_suffixes=['.jinja'],
    ).render(
        dict(
            get_version=importlib.metadata.version,
            config=config.model_dump(exclude_unset=True, exclude_defaults=True, exclude_none=True),
            document=document,
        ),
        pathlib.Path(project_root),
    )


async def render_project(project_root: anyio.Path) -> None:
    config = await load_config(project_root)

    logger.info('Parse OpenAPI document')
    oa_doc = await load_document(project_root, config)
    model = prepare_python_model(oa_doc, config)

    logger.info('Render project')

    from rybak import TreeTemplate
    from rybak.jinja import JinjaAdapter

    template = TreeTemplate(
        JinjaAdapter(
            jinja2.Environment(
                loader=jinja2.loaders.PackageLoader('lapidary.render', package_path='templates/render'),
            )
        ),
        exclude_extend=[
            'includes',
        ],
        remove_suffixes=['.jinja'],
    )

    with RenderProgressBar(model) as event_sink:
        template.render(
            dict(
                model=model,
                get_version=importlib.metadata.version,
            ),
            pathlib.Path(project_root) / 'gen',
            event_sink=event_sink,
            remove_stale=True,
        )


class RenderProgressBar(rybak.EventSink):
    def __init__(self, model: python.ClientModel) -> None:
        self._progress_bar = click.progressbar(
            model.modules,
            label='Rendering modules',
            item_show_func=lambda item: item or '',
            show_pos=True,
        )

    def __enter__(self) -> Any:
        self._progress_bar.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        return self._progress_bar.__exit__(exc_type, exc_val, exc_tb)

    def writing_file(self, template: pathlib.PurePath, target: pathlib.Path) -> None:
        super().writing_file(template, target)
        if str(template) == '{{loop_over(model.modules).file_path}}.py.jinja':
            self._progress_bar.update(1, str(target).split('/')[-2])


async def dump_model(project_root: anyio.Path, process: bool, output: TextIO):
    from pprint import pprint

    config = await load_config(project_root)
    oa_doc = await load_document(project_root, config)

    if not process:
        yaml = ruamel.yaml.YAML(typ='safe')
        yaml.dump(oa_doc, output)

    else:
        py_model = prepare_python_model(oa_doc, config)
        pprint(py_model, output)


def prepare_python_model(oa_doc: Mapping, config: Config) -> python.ClientModel:
    oa_model = openapi.OpenApiModel.model_validate(oa_doc)
    with click.progressbar(
        length=len(oa_model.paths.paths),
        label='Processing paths',
        item_show_func=str,
        show_pos=True,
    ) as pbar:
        logger.info('Prepare python model')
        return OpenApi30Converter(
            python.ModulePath(config.package),
            oa_model,
            str(config.origin) if config.origin else None,
            path_progress=lambda item: pbar.update(1, item),
        ).process()
