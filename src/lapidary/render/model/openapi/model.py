import typing
from collections.abc import Mapping, Sequence
from typing import Annotated

import pydantic
from openapi_pydantic.v3.v3_0 import (
    Components as ComponentsBase,
    Encoding as EncodingBase,
    MediaType as MediaTypeBase,
    OpenAPI as OpenAPIBase,
    Operation as OperationBase,
    Parameter as ParameterPydanticBase,
    ParameterLocation as ParameterLocation,
    PathItem as PathItemBase,
    Reference as ReferenceBase,
    RequestBody as RequestBodyBase,
    Response as ResponseBase,
    Schema as SchemaBase,
    SecurityScheme as SecuritySchemeBase,
)
from openapi_pydantic.v3.v3_0.parameter import ParameterBase as ParameterBaseBase

from .base import (
    ExtendableModel,
    ModelWithAdditionalProperties,
    ModelWithPatternProperties,
    PropertyPattern,
    validate_example_xor_examples,
)


class SecurityScheme(SecuritySchemeBase):
    format: Annotated[str, pydantic.Field(alias='x-lapidary-format')] = '{}'


class Reference[Target](ReferenceBase):
    model_config = pydantic.ConfigDict(frozen=True)


def validate_list_unique(v: Sequence[typing.Any]) -> Sequence[typing.Any]:
    if len(set(v)) != len(v):
        raise ValueError('not unique')
    return v


UniqueListValidator = pydantic.AfterValidator(validate_list_unique)


class Schema(SchemaBase):
    # type == array
    items: 'None | Reference[Schema] | Schema' = None

    # type == object
    properties: 'None | dict[str, Reference[Schema] | Schema]' = None
    additionalProperties: 'None | bool | Reference[Schema] | Schema' = None

    schema_not: 'Annotated[None | Reference[Schema] | Schema, pydantic.Field(alias="not")]' = None
    allOf: 'None | list[Reference[Schema] | Schema]' = None
    oneOf: 'None | list[Reference[Schema] | Schema]' = None
    anyOf: 'None | list[Reference[Schema] | Schema]' = None

    lapidary_name: typing.Annotated[str | None, pydantic.Field(alias='x-lapidary-type-name')] = None


class ParameterBase(ParameterBaseBase):
    content: 'typing.Annotated[dict[str, MediaType] | None, pydantic.Field(max_length=1, min_length=1)]' = None
    param_schema: typing.Annotated[None | Reference[Schema] | Schema, pydantic.Field(alias='schema')] = None

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
    in_: typing.Annotated[ParameterLocation, pydantic.Field(alias='in')] = ParameterLocation.HEADER
    style: str = 'simple'


class Encoding(EncodingBase):
    headers: dict[str, Header] | None = None


class MediaType(MediaTypeBase):
    media_type_schema: typing.Annotated[None | Reference[Schema] | Schema, pydantic.Field(alias='schema')] = None

    @pydantic.model_validator(mode='before')
    @staticmethod
    def _validate(values: Mapping[str, typing.Any]):
        if not isinstance(values, Mapping | MediaType):
            raise TypeError(type(values))
        validate_example_xor_examples(values)
        return values


class Response(ResponseBase):
    headers: Annotated[dict[str, Reference[Header] | Header], pydantic.Field(default_factory=dict)]
    content: 'typing.Annotated[dict[str, MediaType], pydantic.Field(default_factory=dict)]'


class Responses(ExtendableModel, ModelWithPatternProperties):
    responses: typing.Annotated[
        dict[str, Reference[Response] | Response],
        pydantic.Field(default_factory=dict, min_length=1),
        PropertyPattern(r'^[1-5](?:\d{2}|XX)|default$'),
    ]


class Parameter(ParameterBase, ParameterPydanticBase):
    lapidary_name: typing.Annotated[str | None, pydantic.Field(alias='x-lapidary-name')] = None
    explode: bool | None = None

    @property
    def effective_name(self) -> str:
        return self.lapidary_name or self.name

    def __hash__(self) -> int:
        return (hash(self.name) << 2) + hash(self.param_in)


class RequestBody(RequestBodyBase):
    content: 'dict[str, MediaType]'


class Operation(OperationBase):
    parameters: typing.Annotated[
        list[Reference[Parameter] | Parameter], UniqueListValidator, pydantic.Field(default_factory=list)
    ]
    requestBody: Annotated[None | Reference[RequestBody] | RequestBody, pydantic.Field(alias='requestBody')] = None
    responses: Responses
    callbacks: 'dict[str, Reference[Callback] | Callback] | None' = None


class PathItem(PathItemBase):
    parameters: typing.Annotated[
        list[Reference[Parameter] | Parameter], UniqueListValidator, pydantic.Field(default_factory=list)
    ]
    get: Operation | None = None
    put: Operation | None = None
    post: Operation | None = None
    delete: Operation | None = None
    options: Operation | None = None
    head: Operation | None = None
    patch: Operation | None = None
    trace: Operation | None = None


class Paths(ModelWithPatternProperties):
    paths: typing.Annotated[dict[str, PathItem], pydantic.Field(default_factory=dict), PropertyPattern('^/')]


class Callback(ModelWithAdditionalProperties):
    __pydantic_extra__ = dict[str, Reference[PathItem] | PathItem]


class Components(ComponentsBase):
    schemas: Annotated[dict[str, Reference[Schema] | Schema], pydantic.Field(default_factory=dict)]
    responses: dict[str, Reference[Response] | Response] | None = None
    parameters: dict[str, Reference[Parameter] | Parameter] | None = None
    requestBodies: Annotated[
        dict[str, Reference[RequestBody] | RequestBody] | None, pydantic.Field(alias='requestBodies')
    ] = None
    headers: dict[str, Reference[Header] | Header] | None = None
    securitySchemes: dict[str, Reference[SecurityScheme] | SecurityScheme] | None = None
    callbacks: dict[str, Reference[Callback] | Callback] | None = None


class OpenAPI(OpenAPIBase):
    paths: Paths
    components: Components | None = None

    lapidary_headers_global: typing.Annotated[
        dict[str, Header] | None,
        pydantic.Field(
            alias='x-lapidary-headers-global',
            default_factory=dict,
        ),
    ] = None
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
    ] = None
