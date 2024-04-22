import dataclasses as dc
import enum
from collections.abc import Iterable, Mapping
from typing import Any, TypeAlias

from ..openapi import ParameterLocation as ParamLocation
from ..openapi import SecurityRequirement
from ..openapi import Style as ParamStyle
from .type_hint import NONE, TypeHint, type_hint_or_union

MimeType: TypeAlias = str
ResponseCode: TypeAlias = str
MimeMap: TypeAlias = Mapping[MimeType, TypeHint]
ResponseMap: TypeAlias = Mapping[ResponseCode, MimeMap]


@dc.dataclass
class AttributeAnnotation:
    type: TypeHint
    field_props: dict[str, Any]
    style: str | None = None
    explode: bool | None = None
    allowReserved: bool | None = False


@dc.dataclass
class Attribute:
    name: str
    annotation: AttributeAnnotation
    required: bool
    """
    Used for op method params. Required params are rendered before optional, and optional have default value None
    """

    deprecated: bool = False
    """Currently not used"""

    @property
    def dependencies(self) -> Iterable[TypeHint]:
        return [self.annotation.type]


@dc.dataclass
class Auth:
    name: str
    type: str


@dc.dataclass(kw_only=True)
class ApiKeyAuth(Auth):
    key: str
    location: ParamLocation
    format: str
    type: str = 'api_key'


@dc.dataclass(kw_only=True)
class HttpAuth(Auth):
    scheme: str
    bearer_format: str | None
    type: str = 'http'


@dc.dataclass(kw_only=True)
class OpenIdConnectAuth(Auth):
    url: str
    type: str = 'openIdConnect'


@dc.dataclass(kw_only=True)
class OAuth2AuthBase(Auth):
    scopes: dict[str, str]


@dc.dataclass(kw_only=True)
class ImplicitOAuth2Flow(OAuth2AuthBase):
    authorization_url: str
    type: str = 'oauth2_implicit'


@dc.dataclass(kw_only=True)
class PasswordOAuth2Flow(OAuth2AuthBase):
    token_url: str
    refresh_url: str | None = None
    type: str = 'oauth2_password'


@dc.dataclass(kw_only=True)
class AuthorizationCodeOAuth2FLow(OAuth2AuthBase):
    authorization_url: str
    tokenUrl: str
    refresh_url: str | None = None
    type: str = 'oauth2_authorization_code'


@dc.dataclass
class OperationFunction:
    name: str
    method: str
    path: str
    request_body: MimeMap
    params: Iterable['Parameter']
    responses: ResponseMap
    security: Iterable[SecurityRequirement] | None

    @property
    def dependencies(self) -> Iterable[TypeHint]:
        yield self.request_body_type
        for param in self.params:
            yield from param.dependencies
        yield self.response_body_type

    @property
    def request_body_type(self) -> TypeHint:
        if not self.request_body:
            return NONE
        types = self.request_body.values()
        return type_hint_or_union(types)

    @property
    def response_body_type(self) -> TypeHint:
        types = set()
        for mime_map in self.responses.values():
            types.update(set(mime_map.values()))
        return type_hint_or_union(types)


@dc.dataclass(kw_only=True)
class Parameter:
    name: str
    """Python name"""

    alias: str | None
    """Header name"""

    type: TypeHint

    required: bool
    """
    Required params are rendered before optional, and optional have default value None
    """

    in_: ParamLocation
    default: Any = None
    """Default value, used only for global headers."""

    media_type: str | None = None
    style: ParamStyle | None
    explode: bool | None

    @property
    def dependencies(self) -> Iterable[TypeHint]:
        yield self.type


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
    headers: Iterable[tuple[str, str]] = dc.field(default_factory=list)
    response_map: ResponseMap = dc.field(default_factory=dict)
    security: Iterable[SecurityRequirement] | None = None

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
