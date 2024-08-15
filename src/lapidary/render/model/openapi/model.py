import abc
import decimal as dec
import enum
import typing
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Annotated, Literal, Self, cast

import pydantic.alias_generators

from ...json_pointer import decode_json_pointer
from .base import (
    BaseModel,
    ExtendableModel,
    ModelWithAdditionalProperties,
    ModelWithPatternProperties,
    PropertyPattern,
    validate_example_xor_examples,
)


class Reference[Target](BaseModel):
    model_config = pydantic.ConfigDict(
        populate_by_name=True,
    )

    ref: typing.Annotated[str, pydantic.Field(alias='$ref')]


class Contact(ExtendableModel):
    name: str | None = None
    url: str | None = None
    email: str | None = None


class License(ExtendableModel):
    name: str
    url: str | None = None


class ServerVariable(ExtendableModel):
    enum: list[str] | None = None
    default: str
    description: str | None = None


class Type(Enum):
    array = 'array'
    boolean = 'boolean'
    integer = 'integer'
    number = 'number'
    object = 'object'
    string = 'string'


class Discriminator(BaseModel):
    property_name: Annotated[str, pydantic.Field(alias='propertyName')]
    mapping: dict[str, str] | None = None


class XML(ExtendableModel):
    name: str | None = None
    namespace: pydantic.AnyUrl | None = None
    prefix: str | None = None
    attribute: bool | None = False
    wrapped: bool | None = False


class Example(ExtendableModel):
    summary: str | None = None
    description: str | None = None
    value: typing.Any | None = None
    external_value: Annotated[str | None, pydantic.Field(alias='externalValue')] = None


class Style(Enum):
    deepObject = 'deepObject'
    form = 'form'
    label = 'label'
    matrix = 'matrix'
    pipeDelimited = 'pipeDelimited'
    simple = 'simple'
    spaceDelimited = 'spaceDelimited'


class SecurityRequirement(pydantic.RootModel):
    root: typing.Annotated[dict[str, list[str]], pydantic.Field(default_factory=dict)]


class ExternalDocumentation(ExtendableModel):
    description: str | None
    url: str


class ParameterLocation(enum.Enum):
    cookie = 'cookie'
    header = 'header'
    path = 'path'
    query = 'query'


class SecuritySchemeBase(abc.ABC, ExtendableModel):
    model_config = pydantic.ConfigDict(
        alias_generator=pydantic.alias_generators.to_camel,
    )
    type: str
    description: str | None = None


class APIKeySecurityScheme(SecuritySchemeBase):
    type: Literal['apiKey']
    name: str
    in_: typing.Annotated[ParameterLocation, pydantic.Field(alias='in')]

    format: Annotated[str, pydantic.Field(alias='x-lapidary-format')] = '{}'


class HTTPSecurityScheme(SecuritySchemeBase):
    type: Literal['http']
    scheme: str
    bearer_format: str | None = None


class OpenIdConnectSecurityScheme(SecuritySchemeBase):
    type: Literal['openIdConnect']
    open_id_connect_url: str


class ImplicitOAuthFlow(BaseModel):
    authorization_url: Annotated[str, pydantic.Field(alias='authorizationUrl')]
    refresh_url: Annotated[str | None, pydantic.Field(alias='refreshUrl')] = None
    scopes: dict[str, str]


class PasswordOAuthFlow(BaseModel):
    token_url: Annotated[str, pydantic.Field(alias='tokenUrl')]
    refresh_url: Annotated[str | None, pydantic.Field(alias='refreshUrl')] = None
    scopes: dict[str, str] | None = None


class ClientCredentialsFlow(PasswordOAuthFlow):
    pass


class AuthorizationCodeOAuthFlow(BaseModel):
    authorization_url: Annotated[str, pydantic.Field(alias='authorizationUrl')]
    token_url: Annotated[str, pydantic.Field(alias='tokenUrl')]
    refresh_url: Annotated[str | None, pydantic.Field(alias='refreshUrl')] = None
    scopes: dict[str, str] | None = None


class Info(ExtendableModel):
    title: str
    description: str | None = None
    terms_of_service: Annotated[str | None, pydantic.Field(alias='termsOfService')] = None
    contact: Contact | None = None
    license: License | None = None
    version: str


class Server(ExtendableModel):
    url: str
    description: str | None = None
    variables: dict[str, ServerVariable] | None = None


def validate_list_unique(v: Sequence[typing.Any]) -> Sequence[typing.Any]:
    if len(set(v)) != len(v):
        raise ValueError('not unique')
    return v


UniqueListValidator = pydantic.AfterValidator(validate_list_unique)


class Schema(ExtendableModel):
    title: str | None = None
    type: Type | None = None

    # type == number or type == integer
    multiple_of: typing.Annotated[dec.Decimal | None, pydantic.Field(alias='multipleOf', gt=0.0)] = None
    maximum: dec.Decimal | None = None
    exclusive_maximum: Annotated[bool | None, pydantic.Field(alias='exclusiveMaximum')] = False
    minimum: dec.Decimal | None = None
    exclusive_minimum: Annotated[bool | None, pydantic.Field(alias='exclusiveMinimum')] = False

    # type == string
    max_length: typing.Annotated[int | None, pydantic.Field(alias='maxLength', ge=0)] = None
    min_length: typing.Annotated[int, pydantic.Field(alias='minLength', ge=0)] = 0
    pattern: str | None = None

    # type == array
    items: 'None | Reference[Schema] | Schema' = None
    max_items: typing.Annotated[int | None, pydantic.Field(alias='maxItems', ge=0)] = None
    min_Items: typing.Annotated[int | None, pydantic.Field(alias='minItems', ge=0)] = 0
    unique_items: Annotated[bool | None, pydantic.Field(alias='uniqueItems')] = False

    # type == object
    max_properties: typing.Annotated[int | None, pydantic.Field(alias='maxProperties', ge=0)] = None
    min_properties: typing.Annotated[int | None, pydantic.Field(alias='minProperties', ge=0)] = 0
    required: typing.Annotated[list[str], pydantic.Field(min_length=1, default_factory=list), UniqueListValidator]
    properties: 'typing.Annotated[dict[str, Reference[Schema] | Schema], pydantic.Field(default_factory=dict)]'
    additional_properties: 'Annotated[bool | Reference[Schema] | Schema, pydantic.Field(alias="additionalProperties")]' = True

    # type == string or type = number or type == integer
    format: str | None = None

    enum: typing.Annotated[
        list | None,
        pydantic.Field(min_length=1),
    ] = None

    not_: 'Annotated[None | Reference[Schema] | Schema, pydantic.Field(alias="not")]' = None
    all_of: 'Annotated[None | list[Reference[Schema] | Schema], pydantic.Field(alias="allOf")]' = None
    one_of: 'Annotated[None | list[Reference[Schema] | Schema], pydantic.Field(alias="oneOf")]' = None
    any_of: 'Annotated[None | list[Reference[Schema] | Schema], pydantic.Field(alias="anyOf")]' = None

    description: str | None = None
    default: typing.Any = None
    nullable: bool = False
    discriminator: Discriminator | None = None
    read_only: Annotated[bool, pydantic.Field(alias='readOnly')] = False
    write_only: Annotated[bool, pydantic.Field(alias='writeOnly')] = False
    example: typing.Any = None
    external_docs: Annotated[ExternalDocumentation | None, pydantic.Field(alias='externalDocs')] = None
    deprecated: bool = False
    xml: XML | None = None

    lapidary_names: typing.Annotated[
        dict[str | None, typing.Any] | None,
        pydantic.Field(
            alias='x-lapidary-names',
            default_factory=dict,
            description='Mapping of keys used in the JSON document and variable names in the generated Python code. '
            'Applicable to enum values or object properties.',
        ),
    ]
    lapidary_name: typing.Annotated[str | None, pydantic.Field(alias='x-lapidary-type-name')] = None


class Tag(ExtendableModel):
    name: str
    description: str | None = None
    external_docs: Annotated[ExternalDocumentation | None, pydantic.Field(alias='externalDocs')] = None


class Link(ExtendableModel):
    operation_id: Annotated[str | None, pydantic.Field(alias='operationId')] = None
    operation_ref: Annotated[str | None, pydantic.Field(alias='operationRef')] = None
    parameters: dict[str, typing.Any] | None = None
    request_body: Annotated[typing.Any | None, pydantic.Field(alias='requestBody')] = None
    description: str | None = None
    server: Server | None = None


class OAuthFlows(ExtendableModel):
    implicit: ImplicitOAuthFlow | None = None
    password: PasswordOAuthFlow | None = None
    client_credentials: Annotated[ClientCredentialsFlow | None, pydantic.Field(alias='clientCredentials')] = None
    authorization_code: Annotated[AuthorizationCodeOAuthFlow | None, pydantic.Field(alias='authorizationCode')] = None


class OAuth2SecurityScheme(SecuritySchemeBase):
    type: Literal['oauth2']
    flows: OAuthFlows


SecurityScheme: typing.TypeAlias = (
    APIKeySecurityScheme | HTTPSecurityScheme | OAuth2SecurityScheme | OpenIdConnectSecurityScheme
)


class ParameterBase(ExtendableModel):
    in_: typing.Annotated[ParameterLocation, pydantic.Field(alias='in')]
    description: str | None = None
    required: bool = False
    deprecated: bool = False
    allow_empty_value: Annotated[bool, pydantic.Field(alias='allowEmptyValue')] = False

    content: 'typing.Annotated[dict[str, MediaType] | None, pydantic.Field(max_length=1, min_length=1)]' = None

    style: Style | None = None
    explode: bool | None = None
    allow_reserved: Annotated[bool | None, pydantic.Field(alias='allowReserved')] = False
    schema_: typing.Annotated[None | Reference[Schema] | Schema, pydantic.Field(alias='schema')] = None
    example: typing.Any = None
    examples: dict[str, Reference[Example] | Example] | None = None

    @pydantic.model_validator(mode='before')
    @staticmethod
    def _validate(values: Mapping[str, typing.Any]):
        if not isinstance(values, Mapping | MediaType):
            raise TypeError(type(values))
        if 'content' not in values != 'schema' not in values:
            raise ValueError('content or schema required')
        validate_example_xor_examples(values)
        return values


class Header(ParameterBase):
    in_: typing.Annotated[ParameterLocation, pydantic.Field(alias='in')] = ParameterLocation.header
    style: Style = Style.simple


class Encoding(ExtendableModel):
    content_type: Annotated[str | None, pydantic.Field(alias='contentType')] = None
    headers: dict[str, Header] | None = None
    style: Style | None = None
    explode: bool | None = None
    allow_reserved: Annotated[bool | None, pydantic.Field(alias='allowReserved')] = False


class MediaType(ExtendableModel):
    schema_: typing.Annotated[None | Reference[Schema] | Schema, pydantic.Field(alias='schema')] = None
    example: typing.Any | None = None
    examples: dict[str, Reference[Example] | Example] | None = None
    encoding: dict[str, Encoding] | None = None

    @pydantic.model_validator(mode='before')
    @staticmethod
    def _validate(values: Mapping[str, typing.Any]):
        if not isinstance(values, Mapping | MediaType):
            raise TypeError(type(values))
        validate_example_xor_examples(values)
        return values


class Response(ExtendableModel):
    description: str
    headers: Annotated[dict[str, Reference[Header] | Header], pydantic.Field(default_factory=dict)]
    content: 'typing.Annotated[dict[str, MediaType], pydantic.Field(default_factory=dict)]'
    links: dict[str, Reference[Link] | Link] | None = None


class Responses(ExtendableModel, ModelWithPatternProperties):
    responses: typing.Annotated[
        dict[str, Reference[Response] | Response],
        pydantic.Field(default_factory=dict, min_length=1),
        PropertyPattern(r'^[1-5](?:\d{2}|XX)|default$'),
    ]


class Parameter(ParameterBase):
    name: str

    lapidary_name: typing.Annotated[str | None, pydantic.Field(alias='x-lapidary-name')] = None

    @property
    def effective_name(self) -> str:
        return self.lapidary_name or self.name

    def __hash__(self) -> int:
        return (hash(self.name) << 2) + hash(self.in_)


class RequestBody(ExtendableModel):
    description: str | None = None
    content: 'dict[str, MediaType]'
    required: bool | None = False


class Operation(ExtendableModel):
    tags: list[str] | None = None
    summary: str | None = None
    description: str | None = None
    external_docs: Annotated[ExternalDocumentation | None, pydantic.Field(alias='externalDocs')] = None
    operation_id: Annotated[str | None, pydantic.Field(alias='operationId')] = None
    parameters: typing.Annotated[
        list[Reference[Parameter] | Parameter], UniqueListValidator, pydantic.Field(default_factory=list)
    ]
    request_body: Annotated[None | Reference[RequestBody] | RequestBody, pydantic.Field(alias='requestBody')] = None
    responses: Responses
    callbacks: 'dict[str, Reference[Callback] | Callback] | None' = None
    deprecated: bool | None = False
    security: list[SecurityRequirement] | None = None
    servers: list[Server] | None = None


class PathItem(ModelWithAdditionalProperties):
    summary: str | None = None
    description: str | None = None
    servers: list[Server] | None = None
    parameters: typing.Annotated[
        list[Reference[Parameter] | Parameter], UniqueListValidator, pydantic.Field(default_factory=list)
    ]
    __pydantic_extra__: dict[str, Operation]
    """Keys are HTTP methods"""


class Paths(ModelWithPatternProperties):
    paths: typing.Annotated[dict[str, PathItem], pydantic.Field(default_factory=dict), PropertyPattern('^/')]


class Callback(ModelWithAdditionalProperties):
    __pydantic_extra__ = dict[str, Reference[PathItem] | PathItem]


class Components(ExtendableModel):
    schemas: Annotated[dict[str, Reference[Schema] | Schema], pydantic.Field(default_factory=dict)]
    responses: dict[str, Reference[Response] | Response] | None = None
    parameters: dict[str, Reference[Parameter] | Parameter] | None = None
    examples: dict[str, Reference[Example] | Example] | None = None
    request_bodies: Annotated[
        dict[str, Reference[RequestBody] | RequestBody] | None, pydantic.Field(alias='requestBodies')
    ] = None
    headers: dict[str, Reference[Header] | Header] | None = None
    security_schemes: Annotated[
        dict[str, Reference[SecurityScheme] | SecurityScheme] | None, pydantic.Field(alias='securitySchemes')
    ] = None
    links: dict[str, Reference[Link] | Link] | None = None
    callbacks: dict[str, Reference[Callback] | Callback] | None = None


class OpenApiModel(ExtendableModel):
    """
    Validation schema for OpenAPI Specification 3.0.X.
    """

    model_config = pydantic.ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )

    openapi: typing.Annotated[str, pydantic.Field(pattern='^3\\.0\\.\\d(-.+)?$')]
    info: Info
    external_docs: Annotated[ExternalDocumentation | None, pydantic.Field(alias='externalDocs')] = None
    servers: list[Server] = (Server(url='/'),)
    security: list[SecurityRequirement] | None = None
    tags: typing.Annotated[list[Tag] | None, UniqueListValidator] = None
    paths: Paths
    components: Components | None = None

    lapidary_headers_global: typing.Annotated[
        dict[str, Header],
        pydantic.Field(
            alias='x-lapidary-headers-global',
            default_factory=dict,
        ),
    ]
    """Headers added to every request.
    Unlike with operation headers, the default value found in the schema is sent over the wire"""

    lapidary_responses_global: typing.Annotated[
        Responses | None,
        pydantic.Field(
            alias='x-lapidary-responses-global',
            description='Common Responses, added to every operation. '
            'Values in Responses declared in Operations override values in this one.',
            default=None,
        ),
    ]

    def resolve_ref[Target](self, ref: Reference[Target]) -> tuple[Target, str]:
        pointer = ref.ref
        target = self._resolve_ref(pointer)
        stack = [pointer]

        while isinstance(target, Reference):
            pointer = target.ref
            if pointer in stack:
                raise ValueError('Circular references', stack, pointer)
            else:
                stack.append(pointer)
            target = self._resolve_ref(pointer)
        return cast(Target, target), pointer

    def _resolve_ref[Target](self: Self, ref_str: str) -> Target | Reference[Target]:
        """Resolve ref without recursion"""
        obj: typing.Any = self
        for name in ref_str.split('/')[1:]:
            name = decode_json_pointer(name)
            obj = _resolve_name(obj, name)
        return obj


def _resolve_name(src: typing.Any, name: str) -> typing.Any:
    if isinstance(src, Paths) and name in src.paths:
        src = src.paths
    elif isinstance(src, PathItem) and name in src.model_extra:
        src = src.model_extra

    if isinstance(src, Sequence):
        return src[int(name)]
    elif isinstance(src, Mapping):
        return src[name]
    else:
        if hasattr(src, name):
            return getattr(src, name)
        for field_name, field_info in cast(pydantic.BaseModel, src).model_fields.items():
            if name == field_info.alias:
                return getattr(src, field_name)
        else:
            raise AttributeError(name)
