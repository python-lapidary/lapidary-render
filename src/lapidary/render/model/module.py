from dataclasses import dataclass, field

from lapidary.render.model.python.module_path import ModulePath

template_imports = [
    'builtins',
    'pydantic',
    'typing',
    'typing_extensions'
]


@dataclass(frozen=True, kw_only=True)
class AbstractModule:
    path: ModulePath
    imports: list[str] = field(default_factory=list)
