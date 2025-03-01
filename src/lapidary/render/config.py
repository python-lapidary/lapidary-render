import tomllib
from collections.abc import Sequence

import anyio
import pydantic

PYPROJ_TOML = 'pyproject.toml'


class Config(pydantic.BaseModel):
    document_path: str | None = None
    """URL or path relative to ./openapi/"""
    origin: pydantic.AnyHttpUrl | None = None
    """Origin URL in case"""
    package: str


async def load_config(project_root: anyio.Path) -> Config:
    text = await (project_root / PYPROJ_TOML).read_text()
    pyproj = tomllib.loads(text)
    pyproj_dict = pyproj['tool']['lapidary']
    return Config.model_validate(pyproj_dict)
