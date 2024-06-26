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
class AbstractModule[Body](abc.ABC):
    path: ModulePath = dc.field()
    module_type: str
    body: Body = dc.field()

    @property
    @abc.abstractmethod
    def imports(self) -> Iterable[str]:
        pass

    @property
    def rel_path(self) -> str:
        return self.path.to_path()


@dc.dataclass(frozen=True, kw_only=True)
class SchemaModule(AbstractModule[Iterable[SchemaClass]]):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for inline request and for response body for each operation
    """

    module_type: str = 'schema'

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
class AuthModule(AbstractModule[Mapping[str, TypeHint]]):
    module_type = 'auth'

    @property
    def imports(self) -> Iterable[str]:
        yield from ()


@dc.dataclass(frozen=True, kw_only=True)
class ClientModule(AbstractModule[ClientClass]):
    module_type: str = dc.field(default='client')

    @property
    def imports(self) -> Iterable[str]:
        dependencies = GenericTypeHint.union_of(*self.body.dependencies).args  # flatten unions
        imports = sorted({imp for dep in dependencies if dep for imp in dep.imports() if imp not in template_imports})

        return imports


@dc.dataclass(frozen=True, kw_only=True)
class EmptyModule(AbstractModule[None]):
    """Module used to generate empty __init__.py files"""

    module_type: str = dc.field(default='empty')
    body: None = None

    @property
    def imports(self) -> Iterable[str]:
        yield from ()
