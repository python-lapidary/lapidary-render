import typing
from collections.abc import Mapping, Sequence
from enum import Enum

import pydantic
from typing_extensions import Doc

from lapidary.runtime.model.params import ParamLocation

from .base import (
    BaseModel,
    ExtendableModel,
    ModelWithAdditionalProperties,
    ModelWithPatternProperties,
    PropertyPattern,
)
from .ext import LapidaryModelType

__all__ = [
    'APIKeySecurityScheme',
    'AuthorizationCodeOAuthFlow',
    'Callback',
    'ClientCredentialsFlow',
    'Components',
    'Contact',
    'Discriminator',
    'Encoding',
    'Example',
    'ExternalDocumentation',
    'HTTPSecurityScheme',
    'Header',
    'ImplicitOAuthFlow',
    'In',
    'In1',
    'In2',
    'In3',
    'In4',
    'Info',
    'License',
    'Link',
    'MediaType',
    'OAuth2SecurityScheme',
    'OAuthFlows',
    'OpenApiModel',
    'OpenIdConnectSecurityScheme',
    'Operation',
    'Parameter',
    'ParameterBase',
    'ParameterLocation',
    'ParameterLocationItem',
    'ParameterLocationItem1',
    'ParameterLocationItem2',
    'ParameterLocationItem3',
    'PasswordOAuthFlow',
    'PathItem',
    'Paths',
    'Reference',
    'RequestBody',
    'Required',
    'Response',
    'Responses',
    'Schema',
    'SecurityRequirement',
    'SecurityScheme',
    'Server',
    'ServerVariable',
    'Style',
    'Style1',
    'Style2',
    'Style4',
    'Tag',
    'Type',
    'Type1',
    'Type2',
    'Type3',
    'Type4',
    'XML',
]


class Reference[Target](BaseModel):
    model_config = pydantic.ConfigDict(
        populate_by_name=True,
    )

    ref: typing.Annotated[str, pydantic.Field(alias='$ref')]


class Contact(ExtendableModel):
    name: str | None
    url: str | None
    email: pydantic.EmailStr | None


class License(ExtendableModel):
    name: str
    url: str | None


class ServerVariable(ExtendableModel):
    enum: list[str] | None
    default: str
    description: str | None


class Type(Enum):
    array = 'array'
    boolean = 'boolean'
    integer = 'integer'
    number = 'number'
    object = 'object'
    string = 'string'


class Discriminator(pydantic.BaseModel):
    propertyName: str
    mapping: dict[str, str] | None


class XML(ExtendableModel):
    name: str | None
    namespace: pydantic.AnyUrl | None
    prefix: str | None
    attribute: bool | None = False
    wrapped: bool | None = False


class Example(ExtendableModel):
    summary: str | None
    description: str | None
    value: typing.Any | None
    externalValue: str | None


class Style(Enum):
    simple = 'simple'


class SecurityRequirement(pydantic.RootModel):
    root: typing.Annotated[dict[str, list[str]], pydantic.Field(default_factory=dict)]


class ExternalDocumentation(ExtendableModel):
    description: str | None
    url: str


class In(Enum):
    path = 'path'


class Style1(Enum):
    matrix = 'matrix'
    label = 'label'
    simple = 'simple'


class Required(Enum):
    bool_True = True


class ParameterLocationItem(pydantic.BaseModel):
    """
    Parameter in path
    """

    in_: typing.Annotated[In | None, pydantic.Field(alias='in')]
    style: Style1 | None = 'simple'
    required: Required

    class Config:
        extra = pydantic.Extra.forbid
        allow_population_by_field_name = True


class In1(Enum):
    query = 'query'


class Style2(Enum):
    form = 'form'
    spaceDelimited = 'spaceDelimited'
    pipeDelimited = 'pipeDelimited'
    deepObject = 'deepObject'


class ParameterLocationItem1(pydantic.BaseModel):
    """
    Parameter in query
    """

    in_: typing.Annotated[In1 | None, pydantic.Field(alias='in')]
    style: Style2 | None = 'form'

    class Config:
        extra = pydantic.Extra.forbid
        allow_population_by_field_name = True


class In2(Enum):
    header = 'header'


class ParameterLocationItem2(pydantic.BaseModel):
    """
    Parameter in header
    """

    in_: typing.Annotated[In2 | None, pydantic.Field(alias='in')]
    style: Style | None = 'simple'

    class Config:
        extra = pydantic.Extra.forbid
        allow_population_by_field_name = True


class In3(Enum):
    cookie = 'cookie'


class Style4(Enum):
    form = 'form'


class ParameterLocationItem3(pydantic.BaseModel):
    """
    Parameter in cookie
    """

    in_: typing.Annotated[In3 | None, pydantic.Field(alias='in')]
    style: Style4 | None = 'form'

    class Config:
        extra = pydantic.Extra.forbid
        allow_population_by_field_name = True


class ParameterLocation(pydantic.RootModel):
    root: typing.Annotated[
        ParameterLocationItem | ParameterLocationItem1 | ParameterLocationItem2 | ParameterLocationItem3,
        pydantic.Field(description='Parameter location'),
    ]


class Type1(Enum):
    apiKey = 'apiKey'


class In4(Enum):
    header = 'header'
    query = 'query'
    cookie = 'cookie'


class APIKeySecurityScheme(ExtendableModel):
    type: Type1
    name: str
    in_: typing.Annotated[In4, pydantic.Field(alias='in')]
    description: str | None


class Type2(Enum):
    http = 'http'


class HTTPSecurityScheme(ExtendableModel):
    scheme: str
    bearerFormat: str | None
    description: str | None
    type: Type2

    @pydantic.model_validator(mode='after')
    def _validate_bearer_format(self) -> typing.Self:
        if self.scheme.lower() != 'bearer':
            raise ValueError('bearerFormat is only allowed if "schema" is "bearer"')

        return self


class Type3(Enum):
    oauth2 = 'oauth2'


class Type4(Enum):
    openIdConnect = 'openIdConnect'


class OpenIdConnectSecurityScheme(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    type: Type4
    openIdConnectUrl: str
    description: str | None


class ImplicitOAuthFlow(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    authorizationUrl: str
    refreshUrl: str | None
    scopes: dict[str, str]


class PasswordOAuthFlow(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    tokenUrl: str
    refreshUrl: str | None = None
    scopes: dict[str, str] | None = None


class ClientCredentialsFlow(PasswordOAuthFlow):
    pass


class AuthorizationCodeOAuthFlow(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    authorizationUrl: str
    tokenUrl: str
    refreshUrl: str | None = None
    scopes: dict[str, str] | None = None


class Info(ExtendableModel):
    title: str
    description: str | None = None
    termsOfService: str | None = None
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
    multipleOf: typing.Annotated[float | None, pydantic.Field(gt=0.0)] = None
    maximum: float | None = None
    exclusiveMaximum: bool | None = False
    minimum: float | None = None
    exclusiveMinimum: bool | None = False

    # type == string
    maxLength: typing.Annotated[int | None, pydantic.Field(ge=0)] = None
    minLength: typing.Annotated[int, pydantic.Field(ge=0)] = 0
    pattern: str | None = None

    # type == array
    items: 'None | Reference[Schema] | Schema' = None
    maxItems: typing.Annotated[int | None, pydantic.Field(ge=0)] = None
    minItems: typing.Annotated[int | None, pydantic.Field(ge=0)] = 0
    uniqueItems: bool | None = False

    # type == object
    maxProperties: typing.Annotated[int | None, pydantic.Field(ge=0)] = None
    minProperties: typing.Annotated[int | None, pydantic.Field(ge=0)] = 0
    required: typing.Annotated[list[str], pydantic.Field(min_items=1, default_factory=list), UniqueListValidator]
    properties: 'typing.Annotated[dict[str, Reference[Schema] | Schema], pydantic.Field(default_factory=dict)]'
    additionalProperties: 'Reference | Schema | bool' = True

    # type == string or type = number or type == integer
    format: str | None = None

    enum: typing.Annotated[
        list | None,
        pydantic.Field(min_items=1),
    ] = None

    not_: 'typing.Annotated[None | Reference[Schema] | Schema, pydantic.Field(alias="not")]' = None
    allOf: 'list[Reference[Schema] | Schema] | None' = None
    oneOf: 'list[Reference[Schema] | Schema] | None' = None
    anyOf: 'list[Reference[Schema] | Schema] | None' = None

    description: str | None = None
    default: typing.Any | None = None
    nullable: bool | None = False
    discriminator: Discriminator | None = None
    readOnly: bool | None = False
    writeOnly: bool | None = False
    example: typing.Any | None = None
    externalDocs: ExternalDocumentation | None = None
    deprecated: bool | None = False
    xml: XML | None = None

    lapidary_names: typing.Annotated[
        dict[str | None, typing.Any] | None,
        pydantic.Field(
            alias='x-lapidary-names',
            default_factory=dict,
            description='Mapping of keys used in the JSON document and variable names in the generated Python code. '
            'Applicable to enum values or object properties.',
        ),
    ] = None
    lapidary_name: typing.Annotated[str | None, pydantic.Field(alias='x-lapidary-type-name')] = None
    lapidary_model_type: typing.Annotated[LapidaryModelType | None, pydantic.Field(alias='x-lapidary-modelType')] = None


class Tag(ExtendableModel):
    name: str
    description: str | None = None
    externalDocs: ExternalDocumentation | None = None


class OAuthFlows(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    implicit: ImplicitOAuthFlow | None = None
    password: PasswordOAuthFlow | None = None
    clientCredentials: ClientCredentialsFlow | None = None
    authorizationCode: AuthorizationCodeOAuthFlow | None = None


class Link(ExtendableModel):
    operationId: str | None = None
    operationRef: str | None = None
    parameters: dict[str, typing.Any] | None = None
    requestBody: typing.Any | None = None
    description: str | None = None
    server: Server | None = None


class OAuth2SecurityScheme(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    type: Type3
    flows: OAuthFlows
    description: str | None = None


class SecurityScheme(pydantic.RootModel):
    root: APIKeySecurityScheme | HTTPSecurityScheme | OAuth2SecurityScheme | OpenIdConnectSecurityScheme


class ParameterBase(ExtendableModel):
    in_: typing.Annotated[ParamLocation, pydantic.Field(alias='in')]
    description: str | None = None
    required: bool = False
    deprecated: bool = False
    allowEmptyValue: bool = False

    content: 'typing.Annotated[dict[str, MediaType] | None, pydantic.Field(maxProperties=1, minProperties=1)]' = None

    style: str | None = None
    explode: bool | None = None
    allowReserved: bool | None = False
    schema_: typing.Annotated[None | Reference[Schema] | Schema, pydantic.Field(alias='schema')] = None
    example: typing.Any | None = None
    examples: dict[str, Reference | Example] | None = None

    @pydantic.model_validator(mode='before')
    @staticmethod
    def check_schema_xor_content(values: Mapping[str, typing.Any]):
        if 'content' not in values and 'schema' not in values:
            raise ValueError('content or schema required')
        return values


class Header(ParameterBase):
    in_: typing.Annotated[ParamLocation, pydantic.Field(alias='in')] = ParamLocation.header
    style: Style | None = 'simple'


class Encoding(ExtendableModel):
    contentType: str | None = None
    headers: dict[str, Header] | None = None
    style: Style2 | None = None
    explode: bool | None = None
    allowReserved: bool | None = False


class MediaType(ExtendableModel):
    schema_: typing.Annotated[Reference | Schema | None, pydantic.Field(alias='schema')] = None
    example: typing.Any | None = None
    examples: dict[str, Reference | Example] | None = None
    encoding: dict[str, Encoding] | None = None

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_example_xor_examples(cls, values: Mapping[str, typing.Any]):
        if not isinstance(values, Mapping | MediaType):
            raise TypeError(type(values))
        if 'examples' in values and 'example' in values:
            raise ValueError('Only either example or examples is allowed')
        return values


class Response(ExtendableModel):
    description: str
    headers: dict[str, Reference[Header] | Header] | None = None
    content: 'typing.Annotated[dict[str, MediaType], pydantic.Field(default_factory=dict)]'
    links: dict[str, Reference | Link] | None = None


class Responses(ExtendableModel, ModelWithPatternProperties):
    responses: typing.Annotated[
        dict[str, Reference[Response] | Response],
        pydantic.Field(default_factory=dict, min_items=1),
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
    externalDocs: ExternalDocumentation | None = None
    operationId: str | None = None
    parameters: typing.Annotated[
        list[Parameter | Reference[Parameter]], UniqueListValidator, pydantic.Field(default_factory=list)
    ]
    requestBody: None | Reference | RequestBody = None
    responses: Responses
    callbacks: 'dict[str, Reference | Callback] | None' = None
    deprecated: bool | None = False
    security: list[SecurityRequirement] | None = None
    servers: list[Server] | None = None


class PathItem(BaseModel):
    summary: str | None = None
    description: str | None = None
    servers: list[Server] | None = None
    parameters: typing.Annotated[
        list[Parameter | Reference[Parameter]], UniqueListValidator, pydantic.Field(default_factory=list)
    ]
    __pydantic_extra__: dict[str, Operation]


class Paths(ModelWithPatternProperties):
    paths: typing.Annotated[dict[str, PathItem], pydantic.Field(default_factory=dict), PropertyPattern('^/')]


class Callback(ModelWithAdditionalProperties):
    __pydantic_extra__ = dict[str, Reference | PathItem]


class Components(ExtendableModel):
    schemas: dict[str, Reference[Schema] | Schema] | None = None
    responses: dict[str, Reference[Response] | Response] | None = None
    parameters: dict[str, Reference[Parameter] | Parameter] | None = None
    examples: dict[str, Reference[Example] | Example] | None = None
    requestBodies: dict[str, Reference[RequestBody] | RequestBody] | None = None
    headers: dict[str, Reference[Header] | Header] | None = None
    securitySchemes: dict[str, Reference[SecurityScheme] | SecurityScheme] | None = None
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
    externalDocs: ExternalDocumentation | None = None
    servers: list[Server] | None = None
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
        Doc(
            'Headers added to every request. '
            'Unlike with operation headers, the default value found in the schema is sent over the wire'
        ),
    ]

    lapidary_responses_global: typing.Annotated[
        Responses | None,
        pydantic.Field(
            alias='x-lapidary-responses-global',
            description='Common Responses, added to every operation. '
            'Values in Responses declared in Operations override values in this one.',
            default=None,
        ),
    ]
