import tomllib
from pathlib import Path

import pydantic

PYPROJ_TOML = 'pyproject.toml'


class Config(pydantic.BaseModel):
    document_path: str
    package: str
    patches: str = 'sec/patches'


def load_config(project_root: Path) -> Config:
    text = (project_root / PYPROJ_TOML).read_text()
    pyproj = tomllib.loads(text)
    pyproj_dict = pyproj['tool']['lapidary']
    return Config.model_validate(pyproj_dict)
