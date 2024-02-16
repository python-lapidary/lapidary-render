import abc
import dataclasses as dc
import itertools
from collections.abc import Iterable, Mapping

from .model import ClientClass, SchemaClass
from .module_path import ModulePath
from .type_hint import TypeHint

template_imports = [
    'builtins',
    'pydantic',
    'typing',
    'typing_extensions',
]

default_imports = [
    'lapidary.runtime',
    'httpx',
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
        for cls in self.body:
            yield from cls.imports


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
        global_response_type_imports = {
            import_
            for mime_map in self.body.init_method.response_map.values()
            for type_hint in mime_map.values()
            for import_ in type_hint.imports()
        }

        request_response_type_imports = {
            import_
            for func in self.body.methods
            for imports in itertools.chain(
                map(
                    lambda elem: elem.imports(),
                    filter(lambda elem: elem is not None, (func.response_type, func.request_type)),
                )
            )
            for import_ in imports
        }

        param_type_imports = {
            imp
            for attr in self.body.methods
            for t in attr.params
            for imp in t.annotation.type.imports()
            if imp not in default_imports and imp not in template_imports
        }

        imports = list(
            {
                *default_imports,
                *global_response_type_imports,
                *request_response_type_imports,
                *param_type_imports,
            }
        )

        imports.sort()
        return imports
