import logging
import os
import typing
from pathlib import Path

from .config import Config
from .items import extract_items
from .model import openapi

logger = logging.getLogger(__name__)


class RenderModel(typing.TypedDict):
    package: str
    items: list[str]


def mk_model(model: openapi.OpenApiModel, config: Config) -> RenderModel:
    return RenderModel(
        package=config.package,
        items=sorted(list(extract_items(model))),
    )


def ensure_init_py(pkg_path: Path) -> None:
    for dirpath, _, filenames in os.walk(pkg_path):
        if dirpath != str(pkg_path) and '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()
