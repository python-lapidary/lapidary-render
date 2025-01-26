from __future__ import annotations

import dataclasses as dc
import enum
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Literal, TypeAlias

from ..openapi import ParameterLocation as ParamLocation
from .type_hint import AnnotatedType, NameRef, NoneMetaType, union_of

MimeType: TypeAlias = str
ResponseCode: TypeAlias = str
MimeMap: TypeAlias = Mapping[MimeType, AnnotatedType]
SecurityRequirements: TypeAlias = Sequence[Mapping[str, Iterable[str]]]


@dc.dataclass(slots=True, frozen=True)
class AnnotatedVariable:
    """
    Abstract class for function parameters and data class fields
    """

    name: str
    typ: AnnotatedType
    required: bool
    """
    If required, rendered before optional, and optional have default value None
    """
    alias: str | None

    def dependencies(self) -> Iterable[NameRef]:
        yield from self.typ.dependencies()

    def __post_init__(self):
        assert isinstance(self.typ, AnnotatedType)


@dc.dataclass(kw_only=True, frozen=True)
class Auth:
    name: str
    python_name: str
    type: str


@dc.dataclass(kw_only=True, frozen=True)
class ApiKeyAuth(Auth):
    key: str
    location: ParamLocation
    format: str
    type: str = 'api_key'


@dc.dataclass(kw_only=True, frozen=True)
class HttpAuth(Auth):
    scheme: str
    bearer_format: str | None


@dc.dataclass(kw_only=True, frozen=True)
class HttpBasicAuth(Auth):
    scheme: str = 'basic'
    type: str = 'http_basic'


@dc.dataclass(kw_only=True, frozen=True)
class HttpDigestAuth(Auth):
    scheme: str = 'digest'
    type: str = 'http_digest'


@dc.dataclass(kw_only=True, frozen=True)
class OpenIdConnectAuth(Auth):
    url: str
    type: str = 'openid_connect'


@dc.dataclass(kw_only=True, frozen=True)
class OAuth2AuthBase(Auth):
    scopes: Mapping[str, str]


@dc.dataclass(kw_only=True, frozen=True)
class ImplicitOAuth2Flow(OAuth2AuthBase):
    authorization_url: str
    type: str = 'oauth2_implicit'


@dc.dataclass(kw_only=True, frozen=True)
class PasswordOAuth2Flow(OAuth2AuthBase):
    token_url: str
    type: str = 'oauth2_password'


@dc.dataclass(kw_only=True, frozen=True)
class AuthorizationCodeOAuth2Flow(OAuth2AuthBase):
    authorization_url: str
    token_url: str
    type: str = 'oauth2_authorization_code'


@dc.dataclass(kw_only=True, frozen=True)
class ClientCredentialsOAuth2Flow(OAuth2AuthBase):
    token_url: str
    type: str = 'oauth2_client_credentials'


@dc.dataclass(kw_only=True)
class Response:
    content: MimeMap
    headers_type: AnnotatedType

    def __post_init__(self):
        assert isinstance(self.headers_type, AnnotatedType)

    def dependencies(self) -> Iterable[NameRef]:
        yield from self.headers_type.dependencies()
        for typ in self.content.values():
            yield from typ.dependencies()


ResponseMap: TypeAlias = Mapping[ResponseCode, Response]


@dc.dataclass
class OperationFunction:
    # decorator
    method: str
    path: str
    security: SecurityRequirements | None

    # python signature
    name: str
    params: Sequence[Parameter]
    return_type: AnnotatedType

    # lapidary annotations
    # request_body also makes a parameter
    request_body: MimeMap
    responses: ResponseMap

    def dependencies(self) -> Iterable[NameRef]:
        yield from self.request_body_type.dependencies()
        for param in self.params:
            yield from param.dependencies()
        for response in self.responses.values():
            yield from response.dependencies()

    @property
    def request_body_type(self) -> AnnotatedType:
        if not self.request_body:
            return NoneMetaType
        return union_of(*self.request_body.values())


class ParamStyle(enum.Enum):
    simple_string = 'SimpleString'
    simple_multimap = 'SimpleMultimap'
    form = 'Form'
    form_explode = 'FormExplode'


@dc.dataclass(frozen=True, kw_only=True)
class Parameter(AnnotatedVariable):
    """
    HTTP metadata field - headers, query and path parameters
    """

    in_: Literal['Cookie', 'Header', 'Metadata', 'Link', 'Path', 'Query']

    default: Any = None
    """Default value, used only for global headers."""

    media_type: str | None = None
    style: ParamStyle | None


class ModelType(enum.Enum):
    model = 'python'
    exception = 'exception'


@dc.dataclass
class SchemaClass:
    name: str
    base_type: NameRef

    allow_extra: bool = False
    docstr: str | None = None
    fields: list[AnnotatedVariable] = dc.field(default_factory=list)

    def __post_init__(self):
        for field in self.fields:
            assert isinstance(field, AnnotatedVariable)

    def dependencies(self) -> Iterable[NameRef]:
        for prop in self.fields:
            yield from prop.typ.dependencies()


@dc.dataclass
class ClientInit:
    default_auth: str | None = None
    auth_models: Mapping[str, Auth] = dc.field(default_factory=dict)
    base_url: str | None = None

    # FIXME
    # headers: Iterable[tuple[str, str]] = dc.field(default_factory=list)
    # response_map: ResponseMap = dc.field(default_factory=dict)

    security: SecurityRequirements | None = None

    def dependencies(self) -> Iterable[NameRef]:
        yield from ()
        # FIXME
        # for mime_map in self.response_map.values():
        #     yield from mime_map.values()


@dc.dataclass(frozen=True)
class ClientClass:
    init_method: ClientInit
    methods: list[OperationFunction] = dc.field(default_factory=list)

    def dependencies(self) -> Iterable[NameRef]:
        yield from self.init_method.dependencies()
        for fn in self.methods:
            yield from fn.dependencies()


@dc.dataclass(frozen=True)
class MetadataModel:
    name: str
    fields: Iterable[Parameter]

    def dependencies(self) -> Iterable[NameRef]:
        for header in self.fields:
            yield from header.dependencies()
