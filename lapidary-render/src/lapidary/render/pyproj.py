import logging
from importlib.metadata import version
from pathlib import Path

from jinja2 import Environment

from .config import Config, PYPROJ_TOML

logger = logging.getLogger(__name__)


def create_pyproj(project_root: Path, config: Config, title, env: Environment) -> None:
    target = project_root / PYPROJ_TOML
    logger.info('Render %s', target)
    text = env.get_template('pyproject.toml.jinja2').render(
        package=config.package,
        project_name=project_root.name,
        openapi_title=title,
        versions=dict(
            pydantic=version('pydantic'),
            lapidary=version('lapidary'),
            lapidary_render=version('lapidary-render'),
        )
    )
    target.write_text(text)
