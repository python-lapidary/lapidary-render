import abc
import dataclasses as dc
from collections.abc import Iterable, Mapping
from pathlib import PurePath

from .model import Auth, ClientClass, MetadataModel, SchemaClass
from .module_path import ModulePath
from .type_hint import NameRef

template_imports = [
    'builtins',
    'typing',
    'typing_extensions',
    'lapidary.runtime',
]


@dc.dataclass(frozen=True, kw_only=True)
class AbstractModule[Body](abc.ABC):
    path: ModulePath
    body: Body = dc.field(hash=False)

    @abc.abstractmethod
    def dependencies(self) -> Iterable[NameRef]:
        pass

    @property
    def imports(self) -> Iterable[str]:
        return sorted(
            {
                dep.module
                for dep in self.dependencies()
                if dep.module not in template_imports and dep.module != str(self.path)
            }
        )

    @property
    def file_path(self) -> PurePath:
        return self.path.to_path()


@dc.dataclass(frozen=True, kw_only=True)
class AuthModule(AbstractModule[Mapping[str, NameRef]]):
    @property
    def dependencies(self) -> Iterable[NameRef]:  # type: ignore[override]
        return self.body.values()


@dc.dataclass(frozen=True, kw_only=True)
class ClientModule(AbstractModule[ClientClass]):
    def dependencies(self) -> Iterable[NameRef]:
        return self.body.dependencies()


@dc.dataclass(frozen=True, kw_only=True)
class EmptyModule(AbstractModule[None]):
    """Module used to generate empty __init__.py files"""

    body: None = None

    def dependencies(self) -> Iterable[NameRef]:
        return ()


@dc.dataclass(frozen=True, kw_only=True)
class MetadataModule(AbstractModule[Iterable[MetadataModel]]):
    def dependencies(self) -> Iterable[NameRef]:
        for model in self.body:
            yield from model.dependencies()


@dc.dataclass(frozen=True, kw_only=True)
class SchemaModule(AbstractModule[Iterable[SchemaClass]]):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for inline request and for response body for each operation
    """

    def dependencies(self) -> Iterable[NameRef]:
        for schema in self.body:
            yield from schema.dependencies()


@dc.dataclass(frozen=True, kw_only=True)
class SecurityModule(AbstractModule[Mapping[str, Auth]]):
    def dependencies(self) -> Iterable[NameRef]:
        return (
            NameRef(module='httpx', name='BasicAuth'),
            NameRef(module='httpx_auth', name='OAuth2AuthorizationCode'),
            NameRef(module='typing', name='Union'),
            NameRef(module='collections.abc', name='Iterable'),
            NameRef(module='lapidary.runtime', name='NamedAuth'),
        )
