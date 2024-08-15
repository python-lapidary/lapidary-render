import dataclasses as dc
import enum
import typing
from collections.abc import Iterable, Mapping
from typing import Any, Literal, TypeAlias

from ..openapi import ParameterLocation as ParamLocation
from .type_hint import NONE, TypeHint, union_of

MimeType: TypeAlias = str
ResponseCode: TypeAlias = str
MimeMap: TypeAlias = Mapping[MimeType, TypeHint]
SecurityRequirements: TypeAlias = Iterable[Mapping[str, Iterable[str]]]


@dc.dataclass
class Annotation:
    type: TypeHint
    field_props: dict[str, Any]
    style: str | None = None
    explode: bool | None = None
    allowReserved: bool | None = False


@dc.dataclass
class Field:
    name: str
    annotation: Annotation
    required: bool
    """
    Used for op method params. Required params are rendered before optional, and optional have default value None
    """

    deprecated: bool = False
    """Currently not used"""


@dc.dataclass
class Auth:
    name: str
    python_name: str
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


@dc.dataclass(kw_only=True)
class HttpBasicAuth(Auth):
    scheme: str = 'basic'
    type: str = 'http_basic'


@dc.dataclass(kw_only=True)
class HttpDigestAuth(Auth):
    scheme: str = 'digest'
    type: str = 'http_digest'


@dc.dataclass(kw_only=True)
class OpenIdConnectAuth(Auth):
    url: str
    type: str = 'openid_connect'


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
    type: str = 'oauth2_password'


@dc.dataclass(kw_only=True)
class AuthorizationCodeOAuth2Flow(OAuth2AuthBase):
    authorization_url: str
    token_url: str
    type: str = 'oauth2_authorization_code'


@dc.dataclass(kw_only=True)
class ClientCredentialsOAuth2Flow(OAuth2AuthBase):
    token_url: str
    type: str = 'oauth2_client_credentials'


@dc.dataclass(kw_only=True)
class Response:
    content: MimeMap
    headers_type: TypeHint

    def dependencies(self) -> Iterable[TypeHint]:
        yield self.headers_type
        yield from self.content.values()


ResponseMap: typing.TypeAlias = Mapping[ResponseCode, Response]


@dc.dataclass
class OperationFunction:
    # decorator
    method: str
    path: str
    security: SecurityRequirements | None

    # python signature
    name: str
    params: Iterable['MetaField']
    return_type: TypeHint

    # lapidary annotations
    # request_body also makes a parameter
    request_body: MimeMap
    responses: ResponseMap

    def dependencies(self) -> Iterable[TypeHint]:
        yield self.request_body_type
        for param in self.params:
            yield from param.dependencies()
        for response in self.responses.values():
            yield from response.dependencies()

    @property
    def request_body_type(self) -> TypeHint:
        if not self.request_body:
            return NONE
        types = self.request_body.values()
        return union_of(*types)


class ParamStyle(enum.Enum):
    simple_string = 'SimpleString'
    simple_multimap = 'SimpleMultimap'
    form = 'Form'
    form_explode = 'FormExplode'


@dc.dataclass(kw_only=True)
class MetaField:
    """
    HTTP metadata field - headers, query and path parameters
    """

    name: str
    """Python name"""

    alias: str | None
    """Header name"""

    type: TypeHint

    required: bool
    """
    Required params are rendered before optional, and optional have default value None
    """

    annotation: Literal['Cookie', 'Header', 'Metadata', 'Link', 'Path', 'Query']

    default: Any = None
    """Default value, used only for global headers."""

    media_type: str | None = None
    style: ParamStyle | None

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
    docstr: str | None = None
    fields: list[Field] = dc.field(default_factory=list)

    def dependencies(self) -> Iterable[TypeHint]:
        yield self.base_type
        for prop in self.fields:
            yield prop.annotation.type


@dc.dataclass
class ClientInit:
    default_auth: str | None = None
    auth_models: Mapping[str, Auth] = dc.field(default_factory=dict)
    base_url: str | None = None

    # FIXME
    # headers: Iterable[tuple[str, str]] = dc.field(default_factory=list)
    # response_map: ResponseMap = dc.field(default_factory=dict)

    security: SecurityRequirements | None = None

    def dependencies(self) -> Iterable[TypeHint]:
        yield from ()
        # FIXME
        # for mime_map in self.response_map.values():
        #     yield from mime_map.values()


@dc.dataclass(frozen=True)
class ClientClass:
    init_method: ClientInit
    methods: list[OperationFunction] = dc.field(default_factory=list)

    def dependencies(self) -> Iterable[TypeHint]:
        yield from self.init_method.dependencies()
        for fn in self.methods:
            yield from fn.dependencies()


@dc.dataclass(frozen=True)
class ResponseHeader:
    name: str
    alias: str
    type: TypeHint

    def dependencies(self) -> Iterable[TypeHint]:
        yield self.type


@dc.dataclass(frozen=True)
class MetadataModel:
    name: str
    fields: Iterable[MetaField]

    def dependencies(self) -> Iterable[TypeHint]:
        for header in self.fields:
            yield from header.dependencies()
