import tomllib

import anyio
import pydantic

PYPROJ_TOML = 'pyproject.toml'


class Config(pydantic.BaseModel):
    document_path: str | None = None
    origin: pydantic.AnyHttpUrl | None = None
    package: str
    patches: str = 'src/patches'


async def load_config(project_root: anyio.Path) -> Config:
    text = await (project_root / PYPROJ_TOML).read_text()
    pyproj = tomllib.loads(text)
    pyproj_dict = pyproj['tool']['lapidary']
    return Config.model_validate(pyproj_dict)
