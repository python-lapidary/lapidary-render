import dataclasses as dc
import typing

from .auth import AuthModel
from .module import AbstractModule
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
    # path unused


@dc.dataclass
class ClientModel:
    client: ClientModule
    package: str
    schemas: typing.Iterable[SchemaModule]
