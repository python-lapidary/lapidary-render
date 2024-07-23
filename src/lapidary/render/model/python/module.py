import abc
import dataclasses as dc
from collections.abc import Iterable, Mapping

from .model import ClientClass, MetadataModel, SchemaClass
from .module_path import ModulePath
from .type_hint import NONE, TypeHint, flatten

template_imports = [
    'builtins',
    'typing',
    'typing_extensions',
    'lapidary.runtime',
]


@dc.dataclass(frozen=True, kw_only=True)
class AbstractModule[Body](abc.ABC):
    path: ModulePath = dc.field()
    module_type: str
    body: Body = dc.field()

    @abc.abstractmethod
    def dependencies(self) -> Iterable[TypeHint]:
        pass

    @property
    def imports(self) -> Iterable[str]:
        dependencies = flatten(self.dependencies())
        return sorted(
            {
                dep.module
                for dep in dependencies
                if dep.module not in template_imports and dep != NONE and dep.module != str(self.path)
            }
        )

    @property
    def file_path(self) -> str:
        return self.path.to_path()


@dc.dataclass(frozen=True, kw_only=True)
class AuthModule(AbstractModule[Mapping[str, TypeHint]]):
    module_type = 'auth'

    @property
    def dependencies(self) -> Iterable[TypeHint]:
        return self.body.values()


@dc.dataclass(frozen=True, kw_only=True)
class ClientModule(AbstractModule[ClientClass]):
    module_type: str = dc.field(default='client')

    def dependencies(self) -> Iterable[TypeHint]:
        return self.body.dependencies()


@dc.dataclass(frozen=True, kw_only=True)
class EmptyModule(AbstractModule[None]):
    """Module used to generate empty __init__.py files"""

    module_type: str = dc.field(default='empty')
    body: None = None

    def dependencies(self) -> Iterable[TypeHint]:
        return ()


@dc.dataclass(frozen=True, kw_only=True)
class MetadataModule(AbstractModule[Iterable[MetadataModel]]):
    module_type: str = 'metadata'

    def dependencies(self) -> Iterable[TypeHint]:
        for model in self.body:
            yield from model.dependencies()


@dc.dataclass(frozen=True, kw_only=True)
class SchemaModule(AbstractModule[Iterable[SchemaClass]]):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for inline request and for response body for each operation
    """

    module_type: str = 'schema'

    def dependencies(self) -> Iterable[TypeHint]:
        for schema in self.body:
            yield from schema.dependencies()
