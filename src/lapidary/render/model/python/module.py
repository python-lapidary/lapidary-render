import abc
from collections.abc import Iterable
from dataclasses import dataclass

from .module_path import ModulePath

template_imports = [
    'builtins',
    'pydantic',
    'typing',
    'typing_extensions',
]


@dataclass(frozen=True, kw_only=True)
class AbstractModule(abc.ABC):
    path: ModulePath

    @property
    @abc.abstractmethod
    def imports(self) -> Iterable[str]:
        pass
