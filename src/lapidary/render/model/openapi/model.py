import re
import typing
from collections.abc import Iterable, Mapping
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, Union

import pydantic

from .base import DynamicExtendableModel, ExtendableModel
from .ext import LapidaryModelType, PluginModel

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

    ref: Annotated[str, pydantic.Field(alias='$ref')]


class Contact(ExtendableModel):
    name: Optional[str]
    url: Optional[str]
    email: Optional[pydantic.EmailStr]


class License(ExtendableModel):
    name: str
    url: Optional[str]


class ServerVariable(ExtendableModel):
    enum: Optional[List[str]]
    default: str
    description: Optional[str]


class Type(Enum):
    array = 'array'
    boolean = 'boolean'
    integer = 'integer'
    number = 'number'
    object = 'object'
    string = 'string'


class Discriminator(pydantic.BaseModel):
    propertyName: str
    mapping: Optional[Dict[str, str]]


class XML(ExtendableModel):
    name: Optional[str]
    namespace: Optional[pydantic.AnyUrl]
    prefix: Optional[str]
    attribute: Optional[bool] = False
    wrapped: Optional[bool] = False


class Example(ExtendableModel):
    summary: Optional[str]
    description: Optional[str]
    value: Optional[Any]
    externalValue: Optional[str]


class Style(Enum):
    simple = 'simple'


class SecurityRequirement(pydantic.RootModel):
    root: Annotated[dict[str, list[str]], pydantic.Field(default_factory=dict)]


class ExternalDocumentation(ExtendableModel):
    description: Optional[str]
    url: str


class ExampleXORExamples(pydantic.RootModel):
    root: Annotated[
        Any,
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

    in_: Annotated[Optional[In], pydantic.Field(alias='in')]
    style: Optional[Style1] = 'simple'
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

    in_: Annotated[Optional[In1], pydantic.Field(alias='in')]
    style: Optional[Style2] = 'form'

    class Config:
        extra = pydantic.Extra.forbid
        allow_population_by_field_name = True


class In2(Enum):
    header = 'header'


class ParameterLocationItem2(pydantic.BaseModel):
    """
    Parameter in header
    """

    in_: Annotated[Optional[In2], pydantic.Field(alias='in')]
    style: Optional[Style] = 'simple'

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

    in_: Annotated[Optional[In3], pydantic.Field(alias='in')]
    style: Optional[Style4] = 'form'

    class Config:
        extra = pydantic.Extra.forbid
        allow_population_by_field_name = True


class ParameterLocation(pydantic.RootModel):
    root: Annotated[
        Union[
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
    class Config(ExtendableModel.Config):
        allow_population_by_field_name = True

    type: Type1
    name: str
    in_: Annotated[In4, pydantic.Field(alias='in')]
    description: Optional[str]


class Type2(Enum):
    http = 'http'


class HTTPSecurityScheme(ExtendableModel):
    scheme: str
    bearerFormat: Optional[str]
    description: Optional[str]
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
    description: Optional[str]


class ImplicitOAuthFlow(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    authorizationUrl: str
    refreshUrl: Optional[str]
    scopes: Dict[str, str]


class PasswordOAuthFlow(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    tokenUrl: str
    refreshUrl: Optional[str] = None
    scopes: Optional[Dict[str, str]] = None


class ClientCredentialsFlow(PasswordOAuthFlow):
    pass


class AuthorizationCodeOAuthFlow(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    authorizationUrl: str
    tokenUrl: str
    refreshUrl: Optional[str] = None
    scopes: Optional[Dict[str, str]] = None


class Info(ExtendableModel):
    title: str
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[Contact] = None
    license: Optional[License] = None
    version: str


class Server(ExtendableModel):
    url: str
    description: Optional[str] = None
    variables: Optional[Dict[str, ServerVariable]] = None


def validate_list_unique(v: Iterable[Any]) -> Iterable[Any]:
    if sorted(v) != sorted(set(v)):
        raise ValueError('not unique')
    return v


UniqueListValidator = pydantic.AfterValidator(validate_list_unique)


class Schema(ExtendableModel):
    class Config(ExtendableModel.Config):
        allow_population_by_field_name = True

    title: Optional[str] = None
    type: Optional[Type] = None

    # type == number or type == integer
    multipleOf: Annotated[Optional[float], pydantic.Field(gt=0.0)] = None
    maximum: Optional[float] = None
    exclusiveMaximum: Optional[bool] = False
    minimum: Optional[float] = None
    exclusiveMinimum: Optional[bool] = False

    # type == string
    maxLength: Annotated[Optional[int], pydantic.Field(ge=0)] = None
    minLength: Annotated[int, pydantic.Field(ge=0)] = 0
    pattern: Optional[str] = None

    # type == array
    items: 'Optional[Union[Schema, Reference]]' = None
    maxItems: Annotated[Optional[int], pydantic.Field(ge=0)] = None
    minItems: Annotated[Optional[int], pydantic.Field(ge=0)] = 0
    uniqueItems: Optional[bool] = False

    # type == object
    maxProperties: Annotated[Optional[int], pydantic.Field(ge=0)] = None
    minProperties: Annotated[Optional[int], pydantic.Field(ge=0)] = 0
    required: Annotated[Optional[List[str]], pydantic.Field(min_items=1), UniqueListValidator] = None
    properties: 'Optional[Dict[str, Union[Schema, Reference]]]' = None
    additionalProperties: 'Optional[Union[Schema, Reference, bool]]' = True

    # type == string or type = number or type == integer
    format: Optional[str] = None

    enum: Annotated[Optional[List], pydantic.Field(min_items=1),] = None

    not_: 'Annotated[Optional[Union[Schema, Reference]], pydantic.Field(alias="not")]' = None
    allOf: 'Optional[List[Union[Schema, Reference]]]' = None
    oneOf: 'Optional[List[Union[Schema, Reference]]]' = None
    anyOf: 'Optional[List[Union[Schema, Reference]]]' = None

    description: Optional[str] = None
    default: Optional[Any] = None
    nullable: Optional[bool] = False
    discriminator: Optional[Discriminator] = None
    readOnly: Optional[bool] = False
    writeOnly: Optional[bool] = False
    example: Optional[Any] = None
    externalDocs: Optional[ExternalDocumentation] = None
    deprecated: Optional[bool] = False
    xml: Optional[XML] = None

    lapidary_names: Annotated[
        Optional[dict[Union[str, None], Any]],
        pydantic.Field(
            serialization_alias='x-lapidary-names',
            default_factory=dict,
            description="Mapping of keys used in the JSON document and variable names in the generated Python code. "
                        "Applicable to enum values or object properties."
        )
    ] = None
    lapidary_name: Annotated[Optional[str], pydantic.Field(serialization_alias='x-lapidary-type-name')] = None
    lapidary_model_type: Annotated[Optional[LapidaryModelType], pydantic.Field(serialization_alias='x-lapidary-modelType')] = None


class Tag(ExtendableModel):
    name: str
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None


class OAuthFlows(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    implicit: Optional[ImplicitOAuthFlow] = None
    password: Optional[PasswordOAuthFlow] = None
    clientCredentials: Optional[ClientCredentialsFlow] = None
    authorizationCode: Optional[AuthorizationCodeOAuthFlow] = None


class Link(ExtendableModel):
    operationId: Optional[str] = None
    operationRef: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    requestBody: Optional[Any] = None
    description: Optional[str] = None
    server: Optional[Server] = None


class OAuth2SecurityScheme(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    type: Type3
    flows: OAuthFlows
    description: Optional[str] = None


class SecurityScheme(pydantic.RootModel):
    root: Union[
        APIKeySecurityScheme,
        HTTPSecurityScheme,
        OAuth2SecurityScheme,
        OpenIdConnectSecurityScheme,
    ]


class Header(ExtendableModel):
    description: Optional[str]
    required: Optional[bool] = False
    deprecated: Optional[bool] = False
    allowEmptyValue: Optional[bool] = False
    content: 'Annotated[Optional[Dict[str, MediaType]], pydantic.Field(maxProperties=1, minProperties=1)]' = None
    style: Optional[Style] = 'simple'
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = False
    schema_: Annotated[Optional[Union[Schema, Reference]], pydantic.Field(serialization_alias='schema')] = None
    example: Optional[Any] = None
    examples: Optional[Dict[str, Union[Example, Reference]]] = None

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
    headers: Optional[Dict[str, Union[Header, Reference]]] = None
    content: 'Optional[Dict[str, MediaType]]' = None
    links: Optional[Dict[str, Union[Link, Reference]]] = None


class Responses(DynamicExtendableModel[Union[Response, Reference]]):
    __pydantic_extra__: Dict[str, Union[Response, Reference]]


    @classmethod
    def _validate_key(cls, key: str) -> bool:
        return key == 'default' or re.match(r'^[1-5](?:\d{2}|XX)$', key)

    @pydantic.model_validator(mode='before')
    def _validate_min_properties(cls, values):
        if not values:
            raise ValueError('minProperties')
        return values


class Parameter(ExtendableModel):
    model_config = pydantic.ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    name: str
    in_: Annotated[str, pydantic.Field(serialization_alias='in')]
    description: Optional[str] = None
    required: bool = False
    deprecated: bool = False
    allowEmptyValue: bool = False
    content: 'Annotated[Optional[Dict[str, MediaType]], pydantic.Field(maxProperties=1, minProperties=1)]' = None
    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = False
    schema_: Annotated[Optional[Union[Schema, Reference]], pydantic.Field(serialization_alias='schema')] = None
    example: Optional[Any] = None
    examples: Optional[Dict[str, Union[Example, Reference]]] = None

    lapidary_name: Annotated[Union[str, None], pydantic.Field(serialization_alias='x-lapidary-name')] = None

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
    description: Optional[str] = None
    content: 'Dict[str, MediaType]'
    required: Optional[bool] = False


class Encoding(ExtendableModel):
    contentType: Optional[str] = None
    headers: Optional[Dict[str, Header]] = None
    style: Optional[Style2] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = False


class MediaType(ExtendableModel):
    class Config(ExtendableModel.Config):
        allow_population_by_field_name = True

    schema_: Annotated[Optional[Union[Schema, Reference]], pydantic.Field(alias='schema')] = None
    example: Optional[Any] = None
    examples: Optional[Dict[str, Union[Example, Reference]]] = None
    encoding: Optional[Dict[str, Encoding]] = None

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_example_xor_examples(cls, values: Mapping[str, Any]):
        if not (isinstance(values, Mapping) or isinstance(values, MediaType)):
            raise TypeError(type(values))
        if 'examples' in values and 'example' in values:
            raise ValueError('Only either example or examples is allowed')
        return values


class Operation(ExtendableModel):
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None
    operationId: Optional[str] = None
    parameters: Annotated[
        Optional[List[Union[Parameter, Reference]]],
        UniqueListValidator,
    ] = None
    requestBody: Optional[Union[RequestBody, Reference]] = None
    responses: Responses
    callbacks: 'Optional[Dict[str, Union[Callback, Reference]]]' = None
    deprecated: Optional[bool] = False
    security: Optional[List[SecurityRequirement]] = None
    servers: Optional[List[Server]] = None

    paging: Annotated[Optional[PluginModel], pydantic.Field(serialization_alias='x-lapidary-pagingPlugin')] = None


class PathItem(ExtendableModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    servers: Optional[List[Server]] = None
    parameters: Annotated[
        Optional[List[Union[Parameter, Reference]]],
        UniqueListValidator,
    ] = None
    get: Optional[Operation] = None
    put: Optional[Operation] = None
    post: Optional[Operation] = None
    delete: Optional[Operation] = None
    options: Optional[Operation] = None
    head: Optional[Operation] = None
    patch: Optional[Operation] = None
    trace: Optional[Operation] = None


class Paths(DynamicExtendableModel[Union[PathItem, Reference]]):
    @classmethod
    def _validate_key(cls, key: str) -> bool:
        return key.startswith('/')


class Callback(DynamicExtendableModel[Union[PathItem, Reference]]):
    @classmethod
    def _validate_key(cls, key: str) -> bool:
        return True


class Components(ExtendableModel):
    schemas: Optional[Dict[str, Union[Schema, Reference]]] = None
    responses: Optional[Dict[str, Union[Reference, Response]]] = None
    parameters: Optional[Dict[str, Union[Reference, Parameter]]] = None
    examples: Optional[Dict[str, Union[Reference, Example]]] = None
    requestBodies: Optional[Dict[str, Union[Reference, RequestBody]]] = None
    headers: Optional[Dict[str, Union[Reference, Header]]] = None
    securitySchemes: Optional[Dict[str, Union[Reference, SecurityScheme]]] = None
    links: Optional[Dict[str, Union[Reference, Link]]] = None
    callbacks: Optional[Dict[str, Union[Reference, Callback]]] = None


class OpenApiModel(ExtendableModel):
    """
    Validation schema for OpenAPI Specification 3.0.X.
    """

    model_config = pydantic.ConfigDict(
        extra='allow',
        populate_by_name=True,
    )

    openapi: Annotated[str, pydantic.Field(pattern='^3\\.0\\.\\d(-.+)?$')]
    info: Info
    externalDocs: Optional[ExternalDocumentation] = None
    servers: Optional[List[Server]] = None
    security: Optional[List[SecurityRequirement]] = None
    tags: Annotated[Optional[List[Tag]], UniqueListValidator] = None
    paths: Paths
    components: Optional[Components] = None

    lapidary_headers_global: Annotated[
        Optional[Union[
            dict[str, Union[str, list[str]]],
            list[tuple[str, str]]
        ]],
        pydantic.Field(
            serialization_alias='x-lapidary-headers-global',
            description='Headers to add to every request.'
        )
    ] = None

    lapidary_responses_global: Optional[Responses] = pydantic.Field(
        alias='x-lapidary-responses-global',
        description='Base Responses. Values in Responses declared in Operations override values in this one.',
        default=None,
    )
