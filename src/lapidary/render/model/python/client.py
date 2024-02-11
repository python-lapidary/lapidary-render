import dataclasses as dc
import typing
from collections.abc import Iterable
from typing import Self

from .auth import AuthModel
from .module import AbstractModule
from .module_path import ModulePath
from .op import OperationFunctionModel
from .response import ResponseMap
from .schema_class import SchemaModule


@dc.dataclass(frozen=True)
class ClientInit:
    default_auth: str | None
    auth_models: typing.Mapping[str, AuthModel] = dc.field(default_factory=dict)
    base_url: str | None = None
    headers: list[tuple[str, str]] = dc.field(default_factory=list)
    response_map: ResponseMap | None = dc.field(default_factory=dict)


@dc.dataclass(frozen=True)
class ClientClass:
    init_method: ClientInit
    methods: list[OperationFunctionModel] = dc.field(default_factory=list)


@dc.dataclass(frozen=True, kw_only=True)
class ClientModule(AbstractModule):
    body: ClientClass = dc.field()
    model_type = 'client'


@dc.dataclass
class ClientModel:
    client: ClientModule
    package: str
    schemas: typing.Iterable[SchemaModule]

    def packages(self: Self) -> Iterable[ModulePath]:
        packages = {ModulePath(self.package)}

        # for each schema module get its package
        for schema in self.schemas:
            path = schema.path
            while path := path.parent():
                packages.add(path)

        return packages
