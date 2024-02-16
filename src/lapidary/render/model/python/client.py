import dataclasses as dc
import itertools
import typing
from collections.abc import Iterable, MutableSequence
from typing import Self

from .auth import AuthModel
from .module import AbstractModule, template_imports
from .module_path import ModulePath
from .op import OperationFunctionModel
from .response import ResponseMap
from .schema_class import SchemaModule


@dc.dataclass
class ClientInit:
    default_auth: str | None = None
    auth_models: typing.Mapping[str, AuthModel] = dc.field(default_factory=dict)
    base_url: str | None = None
    headers: list[tuple[str, str]] = dc.field(default_factory=list)
    response_map: ResponseMap | None = dc.field(default_factory=dict)


@dc.dataclass(frozen=True)
class ClientClass:
    init_method: ClientInit
    methods: list[OperationFunctionModel] = dc.field(default_factory=list)


default_imports = [
    'lapidary.runtime',
    'httpx',
]


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


@dc.dataclass
class ClientModel:
    client: ClientModule
    package: str
    schemas: MutableSequence[SchemaModule] = dc.field(default_factory=list)

    def packages(self: Self) -> Iterable[ModulePath]:
        packages = {ModulePath(self.package)}

        # for each schema module get its package
        for schema in self.schemas:
            path = schema.path
            while path := path.parent():
                packages.add(path)

        return packages
