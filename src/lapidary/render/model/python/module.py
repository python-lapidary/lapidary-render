import abc
import dataclasses as dc
from collections.abc import Iterable, Mapping

from .model import ClientClass, SchemaClass
from .module_path import ModulePath
from .type_hint import GenericTypeHint, TypeHint

template_imports = [
    'builtins',
    'typing',
    'typing_extensions',
]


@dc.dataclass(frozen=True, kw_only=True)
class AbstractModule(abc.ABC):
    path: ModulePath

    @property
    @abc.abstractmethod
    def imports(self) -> Iterable[str]:
        pass


@dc.dataclass(frozen=True, kw_only=True)
class SchemaModule(AbstractModule):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for inline request and for response body for each operation
    """

    body: list[SchemaClass] = dc.field(default_factory=list)
    model_type: str = 'schema'

    @property
    def imports(self) -> Iterable[str]:
        dependencies = GenericTypeHint.union_of(
            *[dep for cls in self.body for dep in cls.dependencies]
        ).args  # flatten unions
        imports = sorted({imp for dep in dependencies if dep for imp in dep.imports() if imp not in template_imports})
        path_str = str(self.path)
        if path_str in imports:
            imports.remove(path_str)

        return imports


@dc.dataclass(frozen=True, kw_only=True)
class AuthModule(AbstractModule):
    schemes: Mapping[str, TypeHint] = dc.field()
    model_type = 'auth'


@dc.dataclass(frozen=True, kw_only=True)
class ClientModule(AbstractModule):
    body: ClientClass = dc.field()
    model_type = 'client'

    @property
    def imports(self) -> Iterable[str]:
        dependencies = GenericTypeHint.union_of(*self.body.dependencies).args  # flatten unions
        imports = sorted({imp for dep in dependencies if dep for imp in dep.imports() if imp not in template_imports})

        return imports
