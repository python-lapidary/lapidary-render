import dataclasses as dc
import enum
from collections.abc import Iterable, Mapping
from typing import Any

import lapidary.runtime.model.params as runtime

from .type_hint import TypeHint

MimeType = ResponseCode = str
MimeMap = Mapping[MimeType, TypeHint]
ResponseMap = Mapping[ResponseCode, MimeMap]


@dc.dataclass
class AttributeAnnotation:
    type: TypeHint
    field_props: dict[str, Any]
    default: str | None = None
    style: str | None = None
    explode: bool | None = None
    allowReserved: bool | None = False


@dc.dataclass
class Attribute:
    name: str
    annotation: AttributeAnnotation
    deprecated: bool = False
    """Currently not used"""

    required: bool | None = None
    """
    Used for op method params. Required params are rendered before optional, and optional have default value ABSENT
    """


@dc.dataclass
class Auth:
    pass


@dc.dataclass
class ApiKeyAuth(Auth):
    param_name: str
    placement: runtime.ParamLocation


@dc.dataclass
class HttpAuth(Auth):
    scheme: str
    bearer_format: str | None


@dc.dataclass
class OperationFunction:
    name: str
    request_type: TypeHint | None
    params: Iterable[Attribute] = ()
    response_type: TypeHint | None = None
    auth_name: str | None = None
    docstr: str | None = None


@dc.dataclass(kw_only=True)
class Parameter(Attribute):
    in_: runtime.ParamLocation
    default: Any = None
    """Default value, used only for global headers."""

    media_type: str | None = None


class ModelType(enum.Enum):
    model = 'python'
    exception = 'exception'


@dc.dataclass
class SchemaClass:
    class_name: str
    base_type: TypeHint

    allow_extra: bool = False
    has_aliases: bool = False
    docstr: str | None = None
    attributes: list[Attribute] = dc.field(default_factory=list)
    model_type: ModelType = ModelType.model

    @property
    def imports(self) -> Iterable[str]:
        yield from self.base_type.imports()
        for prop in self.attributes:
            yield from prop.annotation.type.imports()


@dc.dataclass
class ClientInit:
    default_auth: str | None = None
    auth_models: Mapping[str, Auth] = dc.field(default_factory=dict)
    base_url: str | None = None
    headers: list[tuple[str, str]] = dc.field(default_factory=list)
    response_map: ResponseMap | None = dc.field(default_factory=dict)


@dc.dataclass(frozen=True)
class ClientClass:
    init_method: ClientInit
    methods: list[OperationFunction] = dc.field(default_factory=list)
