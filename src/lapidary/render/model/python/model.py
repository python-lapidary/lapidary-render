import dataclasses as dc
import enum
from collections.abc import Iterable, Mapping
from typing import Any, TypeAlias

from ..openapi import ParameterLocation as ParamLocation
from .type_hint import TypeHint, type_hint_or_union

MimeType: TypeAlias = str
ResponseCode: TypeAlias = str
MimeMap: TypeAlias = Mapping[MimeType, TypeHint]
ResponseMap: TypeAlias = Mapping[ResponseCode, MimeMap]


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

    @property
    def dependencies(self) -> Iterable[TypeHint]:
        return [self.annotation.type]


@dc.dataclass
class Auth:
    pass


@dc.dataclass
class ApiKeyAuth(Auth):
    param_name: str
    placement: ParamLocation


@dc.dataclass
class HttpAuth(Auth):
    scheme: str
    bearer_format: str | None


@dc.dataclass
class OperationFunction:
    name: str
    method: str
    path: str
    request_body: MimeMap
    params: Mapping[str, 'Parameter']
    responses: ResponseMap

    @property
    def dependencies(self) -> Iterable[TypeHint]:
        yield self.request_body_type
        for param_value in self.params.values():
            yield from param_value.dependencies
        yield self.response_body_type

    @property
    def request_body_type(self) -> TypeHint | None:
        if not self.request_body:
            return None
        types = self.request_body.values()
        return type_hint_or_union(types) if types else None

    @property
    def response_body_type(self) -> TypeHint | None:
        types = set()
        for mime_map in self.responses.values():
            types.update(set(mime_map.values()))
        return type_hint_or_union(types)


@dc.dataclass(kw_only=True)
class Parameter:
    name: str
    annotation: AttributeAnnotation

    required: bool
    """
    Used for op method params. Required params are rendered before optional, and optional have default value ABSENT
    """

    in_: ParamLocation
    default: Any = None
    """Default value, used only for global headers."""

    media_type: str | None = None

    @property
    def dependencies(self) -> Iterable[TypeHint]:
        return [self.annotation.type]


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
    def dependencies(self) -> Iterable[TypeHint]:
        yield self.base_type
        for prop in self.attributes:
            yield from prop.dependencies


@dc.dataclass
class ClientInit:
    default_auth: str | None = None
    auth_models: Mapping[str, Auth] = dc.field(default_factory=dict)
    base_url: str | None = None
    headers: list[tuple[str, str]] = dc.field(default_factory=list)
    response_map: ResponseMap = dc.field(default_factory=dict)

    @property
    def dependencies(self) -> Iterable[TypeHint]:
        for mime_map in self.response_map.values():
            yield from mime_map.values()


@dc.dataclass(frozen=True)
class ClientClass:
    init_method: ClientInit
    methods: list[OperationFunction] = dc.field(default_factory=list)

    @property
    def dependencies(self) -> Iterable[TypeHint]:
        yield from self.init_method.dependencies
        for fn in self.methods:
            yield from fn.dependencies
