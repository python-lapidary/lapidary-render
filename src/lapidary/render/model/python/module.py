import abc
import dataclasses as dc
from collections.abc import Iterable, Mapping

from .model import Auth, ClientClass, MetadataModel, SchemaClass
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
    body: Body = dc.field(hash=False)

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
    @property
    def dependencies(self) -> Iterable[TypeHint]:  # type: ignore[override]
        return self.body.values()


@dc.dataclass(frozen=True, kw_only=True)
class ClientModule(AbstractModule[ClientClass]):
    def dependencies(self) -> Iterable[TypeHint]:
        return self.body.dependencies()


@dc.dataclass(frozen=True, kw_only=True)
class EmptyModule(AbstractModule[None]):
    """Module used to generate empty __init__.py files"""

    body: None = None

    def dependencies(self) -> Iterable[TypeHint]:
        return ()


@dc.dataclass(frozen=True, kw_only=True)
class MetadataModule(AbstractModule[Iterable[MetadataModel]]):
    def dependencies(self) -> Iterable[TypeHint]:
        for model in self.body:
            yield from model.dependencies()


@dc.dataclass(frozen=True, kw_only=True)
class SchemaModule(AbstractModule[Iterable[SchemaClass]]):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for inline request and for response body for each operation
    """

    def dependencies(self) -> Iterable[TypeHint]:
        for schema in self.body:
            yield from schema.dependencies()


@dc.dataclass(frozen=True, kw_only=True)
class SecurityModule(AbstractModule[Mapping[str, Auth]]):
    def dependencies(self) -> Iterable[TypeHint]:
        return (
            TypeHint(module='httpx', name='BasicAuth'),
            TypeHint(module='httpx_auth', name='OAuth2AuthorizationCode'),
            TypeHint(module='typing', name='Union'),
            TypeHint(module='collections.abc', name='Iterable'),
            TypeHint(module='lapidary.runtime', name='NamedAuth'),
        )
