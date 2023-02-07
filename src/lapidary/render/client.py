import logging
import os
from pathlib import Path
from typing import TypedDict

from lapidary.runtime import openapi

from .config import Config
from .items import extract_items

logger = logging.getLogger(__name__)


class RenderModel(TypedDict):
    package: str
    items: list[str]
    signature: str


def mk_model(model: openapi.OpenApiModel, config: Config, signature: str) -> RenderModel:
    return RenderModel(
        package=config.package,
        items=sorted(list(extract_items(model))),
        signature=signature,
    )


def ensure_init_py(pkg_path: Path) -> None:
    for (dirpath, _, filenames) in os.walk(pkg_path):
        if dirpath != str(pkg_path) and '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()
