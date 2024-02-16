import dataclasses as dc
import enum
import typing
from collections.abc import Iterable, Mapping
from typing import Annotated, Any, NamedTuple

import pydantic
from typing_extensions import Doc

import lapidary.runtime.model.params as runtime

from .type_hint import TypeHint

MimeType = ResponseCode = str
MimeMap = Mapping[MimeType, TypeHint]
ResponseMap = Mapping[ResponseCode, MimeMap]


@dc.dataclass(frozen=True)
class AttributeAnnotationModel:
    type: TypeHint
    field_props: dict[str, typing.Any]

    default: str | None = None
    style: str | None = None
    explode: bool | None = None
    allowReserved: bool | None = False


@dc.dataclass
class AttributeModel:
    name: str
    annotation: AttributeAnnotationModel
    deprecated: bool = False
    """Currently not used"""

    required: bool | None = None
    """
    Used for op method params. Required params are rendered before optional, and optional have default value ABSENT
    """


class AuthModel(pydantic.BaseModel):
    pass


class ApiKeyAuthModel(AuthModel):
    param_name: str
    placement: runtime.ParamLocation


class HttpAuthModel(AuthModel):
    scheme: str
    bearer_format: str | None


class OperationFunctionModel(NamedTuple):
    name: str
    request_type: TypeHint | None
    params: Iterable[AttributeModel] = ()
    response_type: TypeHint | None = None
    auth_name: str | None = None
    docstr: str | None = None


@dc.dataclass(kw_only=True)
class Parameter(AttributeModel):
    in_: runtime.ParamLocation
    default: Annotated[Any, Doc('Default value, used only for global headers.')] = None
    media_type: str | None = None


class ModelType(enum.Enum):
    model = 'python'
    param_model = 'param_model'
    exception = 'exception'
    enum = 'enum'


@dc.dataclass(frozen=True)
class SchemaClass:
    class_name: str
    base_type: TypeHint

    allow_extra: bool = False
    has_aliases: bool = False
    docstr: str | None = None
    attributes: list[AttributeModel] = dc.field(default_factory=list)
    model_type: ModelType = ModelType.model

    @property
    def imports(self) -> Iterable[str]:
        yield from self.base_type.imports()
        for prop in self.attributes:
            yield from prop.annotation.type.imports()


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
