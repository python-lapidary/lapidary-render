import typing
from collections.abc import Iterable, Mapping
from enum import Enum

import pydantic

from .base import (
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
    'XML'
]


class Reference(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        populate_by_name=True,
    )

    ref: typing.Annotated[str, pydantic.Field(alias='$ref')]


class Contact(ExtendableModel):
    name: typing.Optional[str]
    url: typing.Optional[str]
    email: typing.Optional[pydantic.EmailStr]


class License(ExtendableModel):
    name: str
    url: typing.Optional[str]


class ServerVariable(ExtendableModel):
    enum: typing.Optional[typing.List[str]]
    default: str
    description: typing.Optional[str]


class Type(Enum):
    array = 'array'
    boolean = 'boolean'
    integer = 'integer'
    number = 'number'
    object = 'object'
    string = 'string'


class Discriminator(pydantic.BaseModel):
    propertyName: str
    mapping: typing.Optional[typing.Dict[str, str]]


class XML(ExtendableModel):
    name: typing.Optional[str]
    namespace: typing.Optional[pydantic.AnyUrl]
    prefix: typing.Optional[str]
    attribute: typing.Optional[bool] = False
    wrapped: typing.Optional[bool] = False


class Example(ExtendableModel):
    summary: typing.Optional[str]
    description: typing.Optional[str]
    value: typing.Optional[typing.Any]
    externalValue: typing.Optional[str]


class Style(Enum):
    simple = 'simple'


class SecurityRequirement(pydantic.RootModel):
    root: typing.Annotated[dict[str, list[str]], pydantic.Field(default_factory=dict)]


class ExternalDocumentation(ExtendableModel):
    description: typing.Optional[str]
    url: str


class ExampleXORExamples(pydantic.RootModel):
    root: typing.Annotated[
        typing.Any,
        pydantic.Field(
            description='Example and examples are mutually exclusive',
            not_={'required': ['example', 'examples']},
        ),
    ]


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

    in_: typing.Annotated[typing.Optional[In], pydantic.Field(alias='in')]
    style: typing.Optional[Style1] = 'simple'
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

    in_: typing.Annotated[typing.Optional[In1], pydantic.Field(alias='in')]
    style: typing.Optional[Style2] = 'form'

    class Config:
        extra = pydantic.Extra.forbid
        allow_population_by_field_name = True


class In2(Enum):
    header = 'header'


class ParameterLocationItem2(pydantic.BaseModel):
    """
    Parameter in header
    """

    in_: typing.Annotated[typing.Optional[In2], pydantic.Field(alias='in')]
    style: typing.Optional[Style] = 'simple'

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

    in_: typing.Annotated[typing.Optional[In3], pydantic.Field(alias='in')]
    style: typing.Optional[Style4] = 'form'

    class Config:
        extra = pydantic.Extra.forbid
        allow_population_by_field_name = True


class ParameterLocation(pydantic.RootModel):
    root: typing.Annotated[
        typing.Union[
            ParameterLocationItem,
            ParameterLocationItem1,
            ParameterLocationItem2,
            ParameterLocationItem3,
        ],
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
    description: typing.Optional[str]


class Type2(Enum):
    http = 'http'


class HTTPSecurityScheme(ExtendableModel):
    scheme: str
    bearerFormat: typing.Optional[str]
    description: typing.Optional[str]
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
    description: typing.Optional[str]


class ImplicitOAuthFlow(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    authorizationUrl: str
    refreshUrl: typing.Optional[str]
    scopes: typing.Dict[str, str]


class PasswordOAuthFlow(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    tokenUrl: str
    refreshUrl: typing.Optional[str] = None
    scopes: typing.Optional[typing.Dict[str, str]] = None


class ClientCredentialsFlow(PasswordOAuthFlow):
    pass


class AuthorizationCodeOAuthFlow(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    authorizationUrl: str
    tokenUrl: str
    refreshUrl: typing.Optional[str] = None
    scopes: typing.Optional[typing.Dict[str, str]] = None


class Info(ExtendableModel):
    title: str
    description: typing.Optional[str] = None
    termsOfService: typing.Optional[str] = None
    contact: typing.Optional[Contact] = None
    license: typing.Optional[License] = None
    version: str


class Server(ExtendableModel):
    url: str
    description: typing.Optional[str] = None
    variables: typing.Optional[typing.Dict[str, ServerVariable]] = None


def validate_list_unique(v: Iterable[typing.Any]) -> Iterable[typing.Any]:
    if sorted(v) != sorted(set(v)):
        raise ValueError('not unique')
    return v


UniqueListValidator = pydantic.AfterValidator(validate_list_unique)


class Schema(ExtendableModel):
    title: typing.Optional[str] = None
    type: typing.Optional[Type] = None

    # type == number or type == integer
    multipleOf: typing.Annotated[typing.Optional[float], pydantic.Field(gt=0.0)] = None
    maximum: typing.Optional[float] = None
    exclusiveMaximum: typing.Optional[bool] = False
    minimum: typing.Optional[float] = None
    exclusiveMinimum: typing.Optional[bool] = False

    # type == string
    maxLength: typing.Annotated[typing.Optional[int], pydantic.Field(ge=0)] = None
    minLength: typing.Annotated[int, pydantic.Field(ge=0)] = 0
    pattern: typing.Optional[str] = None

    # type == array
    items: 'typing.Union[None, Reference, Schema]' = None
    maxItems: typing.Annotated[typing.Optional[int], pydantic.Field(ge=0)] = None
    minItems: typing.Annotated[typing.Optional[int], pydantic.Field(ge=0)] = 0
    uniqueItems: typing.Optional[bool] = False

    # type == object
    maxProperties: typing.Annotated[typing.Optional[int], pydantic.Field(ge=0)] = None
    minProperties: typing.Annotated[typing.Optional[int], pydantic.Field(ge=0)] = 0
    required: typing.Annotated[typing.Optional[typing.List[str]], pydantic.Field(min_items=1), UniqueListValidator] = None
    properties: 'typing.Optional[typing.Dict[str, typing.Union[Reference, Schema]]]' = None
    additionalProperties: 'typing.Union[Reference, Schema, bool]' = True

    # type == string or type = number or type == integer
    format: typing.Optional[str] = None

    enum: typing.Annotated[typing.Optional[typing.List], pydantic.Field(min_items=1),] = None

    not_: 'typing.Annotated[typing.Union[None, Reference, Schema], pydantic.Field(alias="not")]' = None
    allOf: 'typing.Optional[typing.List[typing.Union[Reference, Schema]]]' = None
    oneOf: 'typing.Optional[typing.List[typing.Union[Reference, Schema]]]' = None
    anyOf: 'typing.Optional[typing.List[typing.Union[Reference, Schema]]]' = None

    description: typing.Optional[str] = None
    default: typing.Optional[typing.Any] = None
    nullable: typing.Optional[bool] = False
    discriminator: typing.Optional[Discriminator] = None
    readOnly: typing.Optional[bool] = False
    writeOnly: typing.Optional[bool] = False
    example: typing.Optional[typing.Any] = None
    externalDocs: typing.Optional[ExternalDocumentation] = None
    deprecated: typing.Optional[bool] = False
    xml: typing.Optional[XML] = None

    lapidary_names: typing.Annotated[
        typing.Optional[dict[typing.Union[str, None], typing.Any]],
        pydantic.Field(
            alias='x-lapidary-names',
            default_factory=dict,
            description="Mapping of keys used in the JSON document and variable names in the generated Python code. "
                        "Applicable to enum values or object properties."
        )
    ] = None
    lapidary_name: typing.Annotated[typing.Optional[str], pydantic.Field(alias='x-lapidary-type-name')] = None
    lapidary_model_type: typing.Annotated[typing.Optional[LapidaryModelType], pydantic.Field(alias='x-lapidary-modelType')] = None


class Tag(ExtendableModel):
    name: str
    description: typing.Optional[str] = None
    externalDocs: typing.Optional[ExternalDocumentation] = None


class OAuthFlows(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    implicit: typing.Optional[ImplicitOAuthFlow] = None
    password: typing.Optional[PasswordOAuthFlow] = None
    clientCredentials: typing.Optional[ClientCredentialsFlow] = None
    authorizationCode: typing.Optional[AuthorizationCodeOAuthFlow] = None


class Link(ExtendableModel):
    operationId: typing.Optional[str] = None
    operationRef: typing.Optional[str] = None
    parameters: typing.Optional[typing.Dict[str, typing.Any]] = None
    requestBody: typing.Optional[typing.Any] = None
    description: typing.Optional[str] = None
    server: typing.Optional[Server] = None


class OAuth2SecurityScheme(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    type: Type3
    flows: OAuthFlows
    description: typing.Optional[str] = None


class SecurityScheme(pydantic.RootModel):
    root: typing.Union[
        APIKeySecurityScheme,
        HTTPSecurityScheme,
        OAuth2SecurityScheme,
        OpenIdConnectSecurityScheme,
    ]


class Header(ExtendableModel):
    description: typing.Optional[str]
    required: typing.Optional[bool] = False
    deprecated: typing.Optional[bool] = False
    allowEmptyValue: typing.Optional[bool] = False
    content: 'typing.Annotated[typing.Optional[typing.Dict[str, MediaType]], pydantic.Field(maxProperties=1, minProperties=1)]' = None
    style: typing.Optional[Style] = 'simple'
    explode: typing.Optional[bool] = None
    allowReserved: typing.Optional[bool] = False
    schema_: typing.Annotated[typing.Union[None, Reference, Schema], pydantic.Field(alias='schema')] = None
    example: typing.Optional[typing.Any] = None
    examples: typing.Optional[typing.Dict[str, typing.Union[Reference, Example]]] = None

    @pydantic.model_validator(mode='before')
    @staticmethod
    def check_schema_xor_content(values: Mapping[str, typing.Any]):
        if 'content' in values:
            if fields := set(values.keys()).intersection(
                'style', 'explode', 'allowReserved', 'schema', 'example', 'examples'
            ):
                raise ValueError(f'{", ".join(fields)} not allowed when content is present')
        return values


class Response(ExtendableModel):
    description: str
    headers: typing.Optional[typing.Dict[str, typing.Union[Reference, Header]]] = None
    content: 'typing.Optional[typing.Dict[str, MediaType]]' = None
    links: typing.Optional[typing.Dict[str, typing.Union[Reference, Link]]] = None


class Responses(ExtendableModel, ModelWithPatternProperties):
    responses: typing.Annotated[
        typing.Dict[str, typing.Union[Reference, Response]],
        pydantic.Field(default_factory=dict, min_items=1),
        PropertyPattern(r'^[1-5](?:\d{2}|XX)|default$'),
    ]


class Parameter(ExtendableModel):
    model_config = pydantic.ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    name: str
    in_: typing.Annotated[str, pydantic.Field(alias='in')]
    description: typing.Optional[str] = None
    required: bool = False
    deprecated: bool = False
    allowEmptyValue: bool = False
    content: 'typing.Annotated[typing.Optional[typing.Dict[str, MediaType]], pydantic.Field(maxProperties=1, minProperties=1)]' = None
    style: typing.Optional[str] = None
    explode: typing.Optional[bool] = None
    allowReserved: typing.Optional[bool] = False
    schema_: typing.Annotated[typing.Union[None, Reference, Schema], pydantic.Field(alias='schema')] = None
    example: typing.Optional[typing.Any] = None
    examples: typing.Optional[typing.Dict[str, typing.Union[Reference, Example]]] = None

    lapidary_name: typing.Annotated[typing.Union[str, None], pydantic.Field(alias='x-lapidary-name')] = None

    @pydantic.model_validator(mode='before')
    @staticmethod
    def check_schema_xor_content(values: Mapping[str, typing.Any]):
        if 'content' in values:
            if fields := set(values.keys()).intersection(
                'style', 'explode', 'allowReserved', 'schema', 'example', 'examples'
            ):
                raise ValueError(f'{", ".join(fields)} not allowed when content is present')
        return values

    @property
    def effective_name(self) -> str:
        return self.lapidary_name or self.name


class RequestBody(ExtendableModel):
    description: typing.Optional[str] = None
    content: 'typing.Dict[str, MediaType]'
    required: typing.Optional[bool] = False


class Encoding(ExtendableModel):
    contentType: typing.Optional[str] = None
    headers: typing.Optional[typing.Dict[str, Header]] = None
    style: typing.Optional[Style2] = None
    explode: typing.Optional[bool] = None
    allowReserved: typing.Optional[bool] = False


class MediaType(ExtendableModel):
    schema_: typing.Annotated[typing.Union[Reference, Schema, None], pydantic.Field(alias='schema')] = None
    example: typing.Optional[typing.Any] = None
    examples: typing.Optional[typing.Dict[str, typing.Union[Reference, Example]]] = None
    encoding: typing.Optional[typing.Dict[str, Encoding]] = None

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_example_xor_examples(cls, values: Mapping[str, typing.Any]):
        if not (isinstance(values, Mapping) or isinstance(values, MediaType)):
            raise TypeError(type(values))
        if 'examples' in values and 'example' in values:
            raise ValueError('Only either example or examples is allowed')
        return values


class Operation(ExtendableModel):
    tags: typing.Optional[typing.List[str]] = None
    summary: typing.Optional[str] = None
    description: typing.Optional[str] = None
    externalDocs: typing.Optional[ExternalDocumentation] = None
    operationId: typing.Optional[str] = None
    parameters: typing.Annotated[
        typing.Optional[typing.List[typing.Union[Reference, Parameter]]],
        UniqueListValidator,
    ] = None
    requestBody: typing.Union[None, Reference, RequestBody] = None
    responses: Responses
    callbacks: 'typing.Optional[typing.Dict[str, typing.Union[Reference, Callback]]]' = None
    deprecated: typing.Optional[bool] = False
    security: typing.Optional[typing.List[SecurityRequirement]] = None
    servers: typing.Optional[typing.List[Server]] = None


class PathItem(ExtendableModel):
    summary: typing.Optional[str] = None
    description: typing.Optional[str] = None
    servers: typing.Optional[typing.List[Server]] = None
    parameters: typing.Annotated[
        typing.Optional[typing.List[typing.Union[Reference, Parameter]]],
        UniqueListValidator,
    ] = None
    get: typing.Optional[Operation] = None
    put: typing.Optional[Operation] = None
    post: typing.Optional[Operation] = None
    delete: typing.Optional[Operation] = None
    options: typing.Optional[Operation] = None
    head: typing.Optional[Operation] = None
    patch: typing.Optional[Operation] = None
    trace: typing.Optional[Operation] = None


class Paths(ModelWithPatternProperties):
    paths: typing.Annotated[dict[str, PathItem], pydantic.Field(default_factory=dict), PropertyPattern('^/')]


class Callback(ModelWithAdditionalProperties):
    __pydantic_extra__ = dict[str, typing.Union[Reference, PathItem]]


class Components(ExtendableModel):
    schemas: typing.Optional[typing.Dict[str, typing.Union[Reference, Schema]]] = None
    responses: typing.Optional[typing.Dict[str, typing.Union[Reference, Response]]] = None
    parameters: typing.Optional[typing.Dict[str, typing.Union[Reference, Parameter]]] = None
    examples: typing.Optional[typing.Dict[str, typing.Union[Reference, Example]]] = None
    requestBodies: typing.Optional[typing.Dict[str, typing.Union[Reference, RequestBody]]] = None
    headers: typing.Optional[typing.Dict[str, typing.Union[Reference, Header]]] = None
    securitySchemes: typing.Optional[typing.Dict[str, typing.Union[Reference, SecurityScheme]]] = None
    links: typing.Optional[typing.Dict[str, typing.Union[Reference, Link]]] = None
    callbacks: typing.Optional[typing.Dict[str, typing.Union[Reference, Callback]]] = None


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
    externalDocs: typing.Optional[ExternalDocumentation] = None
    servers: typing.Optional[typing.List[Server]] = None
    security: typing.Optional[typing.List[SecurityRequirement]] = None
    tags: typing.Annotated[typing.Optional[typing.List[Tag]], UniqueListValidator] = None
    paths: Paths
    components: typing.Optional[Components] = None

    lapidary_headers_global: typing.Annotated[
        typing.Optional[typing.Union[
            dict[str, typing.Union[str, list[str]]],
            list[tuple[str, str]]
        ]],
        pydantic.Field(
            alias='x-lapidary-headers-global',
            description='Headers to add to every request.',
            default=None,
        )
    ]

    lapidary_responses_global: typing.Annotated[typing.Optional[Responses], pydantic.Field(
        alias='x-lapidary-responses-global',
        description='Base Responses. Values in Responses declared in Operations override values in this one.',
        default=None,
    )]
