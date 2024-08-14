import functools
import itertools
import logging
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from typing import Any, cast

from mimeparse import parse_media_range

from .. import json_pointer, names
from . import openapi, python
from .python import type_hint
from .refs import resolve_ref
from .schema import OpenApi30SchemaConverter, resolve_type_hint
from .stack import Stack

logger = logging.getLogger(__name__)


class OpenApi30Converter:
    def __init__(
        self,
        root_package: python.ModulePath,
        source: openapi.OpenApiModel,
        origin: str | None,
        schema_converter: OpenApi30SchemaConverter | None = None,
        path_progress: Callable[[Any], None] | None = None,
    ):
        self.root_package = root_package
        self.global_headers: dict[str, python.MetaField] = {}
        self.global_responses: dict[python.ResponseCode, python.Response]
        self.src = source
        self._origin = origin
        self._path_progress = path_progress

        self.schema_converter = schema_converter or OpenApi30SchemaConverter(self.root_package, self.resolve_ref)

        self.target = python.ClientModel(
            client=python.ClientModule(
                path=root_package,
                body=python.ClientClass(init_method=python.ClientInit()),
            ),
            package=str(root_package),
        )

        self._response_cache: MutableMapping[Stack, python.Response] = {}

    def process(self) -> python.ClientModel:
        stack = Stack()

        map_process(
            self.src,
            stack,
            {
                'servers': self.process_servers,
                'lapidary_responses_global': self.process_global_responses,
                'lapidary_headers_global': self.process_global_headers,
                'security': self.process_global_security,
                'paths': self.process_paths,
            },
        )

        self.target.model_modules.extend(self.schema_converter.schema_modules)
        return self.target

    def process_servers(self, value: list[openapi.Server] | None, stack: Stack) -> None:
        logger.debug('Process servers %s', stack)

        if not value:
            logger.warning('No servers found')
            return
        if len(value) > 1:
            logger.warning('Multiple servers found, using the first')

        server = value[0]
        server_url = server.url
        if server.variables:
            server_url = server_url.format(**{name: var.default for name, var in server.variables.items()})

        if self._origin:
            from urllib.parse import urljoin

            server_url = urljoin(self._origin, server_url)

        self.target.client.body.init_method.base_url = server_url

    def process_global_headers(self, value: Mapping[str, openapi.Header], stack: Stack) -> None:
        logger.debug('Process global headers %s', stack)
        if not value:
            return

        for header_name, header in value.items():
            self.global_headers[header_name] = self.process_parameter(header, stack.push(header_name))

    def process_global_responses(self, value: openapi.Responses | None, stack: Stack) -> None:
        logger.debug('Process global responses %s', stack)
        if not value:
            return

        self.global_responses = {
            code: self.process_response(response, stack.push(code)) for code, response in value.responses.items()
        }

    def _process_schema_or_content(
        self,
        value: openapi.ParameterBase,
        stack: Stack,
    ) -> tuple[python.TypeHint, str | None]:
        if value.schema_ and value.content:
            raise ValueError()
        if value.schema_:
            return self.schema_converter.process_schema(value.schema_, stack.push('schema'), value.required), None
        elif value.content:
            media_type, media_type_obj = next(iter(value.content.items()))
            # encoding = media_type_obj.encoding
            return self.schema_converter.process_schema(
                media_type_obj.schema_, stack.push('content', media_type), value.required
            ), media_type
        else:
            raise TypeError(f'{stack}: schema or content is required')

    # Not providing process_parameters (plural) as each caller calls it in a different context
    # (list, map or map with defaults)

    @resolve_ref
    def process_parameter(self, value: openapi.Parameter, stack: Stack) -> python.MetaField:
        logger.debug('process_parameter %s', stack)

        if not isinstance(value, openapi.ParameterBase):
            raise TypeError(f'Expected Parameter object at {stack}, got {type(value).__name__}.')

        typ, media_type = self._process_schema_or_content(value, stack)

        return python.MetaField(
            name=parameter_name(value),
            alias=value.name,
            type=typ,
            annotation=value.in_.value.capitalize(),
            style=param_style(value.style, value.explode, value.in_, stack),
            required=value.required,
            media_type=media_type,
        )

    def process_paths(self, value: openapi.Paths, stack: Stack) -> None:
        for path, path_item in value.paths.items():
            self.process_path(path_item, stack.push(json_pointer.encode_json_pointer(path)))

    def process_path(
        self,
        value: openapi.PathItem,
        stack: Stack,
    ) -> None:
        common_params_stack = stack.push('parameters')
        common_params = {
            param.name: self.process_parameter(param, common_params_stack.push(str(idx)))
            for idx, param in enumerate(value.parameters)
        }

        for method, operation in value.model_extra.items():
            self.process_operation(operation, stack.push(method), common_params)
        self._path_progress(json_pointer.decode_json_pointer(stack.top()))

    @resolve_ref
    def process_request_body(self, value: openapi.RequestBody, stack: Stack) -> python.MimeMap:
        # TODO handle required
        return self.process_content(value.content, stack.push('content'))

    def process_responses(self, value: openapi.Responses, stack: Stack) -> python.ResponseMap:
        return {code: self.process_response(response, stack.push(code)) for code, response in value.responses.items()}

    @resolve_ref
    def process_response(
        self,
        value: openapi.Response,
        stack: Stack,
    ) -> python.Response:
        assert isinstance(value, openapi.Response)

        if response := self._response_cache.get(stack):
            return response

        response = python.Response(
            content=self.process_content(value.content, stack.push('content')),
            headers_type=self.process_headers(value.headers, stack.push('headers')),
        )
        self._response_cache[stack] = response
        return response

    def process_headers(self, value: Mapping[str, openapi.Header], stack: Stack) -> python.TypeHint:
        headers = [self.process_header(header, stack.push(name)) for name, header in value.items()]
        if not headers:
            return python.NONE
        model = python.MetadataModel('ResponseMetadata', headers) if headers else None
        typ = resolve_type_hint(str(self.root_package), stack.push('ResponseMetadata'))

        self.target.model_modules.append(
            python.MetadataModule(
                path=python.ModulePath(typ.module, is_module=True),
                body=[model],
            )
        )
        return typ

    @resolve_ref
    def process_header(self, value: openapi.Header, stack: Stack) -> python.MetaField:
        alias = stack.top()

        typ, _ = self._process_schema_or_content(value, stack)

        python_name = names.maybe_mangle_name(alias)
        return python.MetaField(
            name=python_name,
            alias=alias if python_name != alias else None,
            type=typ,
            annotation='Header',
            required=value.required,
            style=param_style(value.style, value.explode, value.in_, stack),
        )

    def process_content(self, value: Mapping[str, openapi.MediaType], stack: Stack) -> python.MimeMap:
        """Returns: {mime_type: response body type hint}"""
        types = {}
        for mime, media_type in value.items():
            mime_parsed = parse_media_range(mime)
            if mime_parsed[:2] != ('application', 'json'):
                continue
            types[mime] = self.schema_converter.process_schema(media_type.schema_, stack.push(mime, 'schema'))
        return types

    def process_operation(
        self,
        value: openapi.Operation,
        stack: Stack,
        common_params: Mapping[str, python.MetaField],
    ) -> None:
        logger.debug('Process operation %s', stack)

        if not value.operation_id:
            raise ValueError(f'{stack}: operationId is required')

        params = self._mk_params(value.parameters, stack.push('parameters'), common_params)

        request_body = (
            self.process_request_body(value.request_body, stack.push('requestBody')) if value.request_body else {}
        )
        responses = self.process_responses(value.responses, stack.push('responses'))
        security = self.process_security(value.security, stack.push('security'))

        return_types = set()
        for status_code, response in responses.items():
            # Don't include error responses in the return type
            if status_code[0] in ('4', '5'):
                continue

            body_type = type_hint.union_of(*response.content.values())
            return_types.add(type_hint.tuple_of(body_type, response.headers_type))

        model = python.OperationFunction(
            name=value.operation_id,
            method=stack.top(),
            path=json_pointer.decode_json_pointer(stack[-2]),
            request_body=request_body,
            params=params,
            responses=responses,
            return_type=type_hint.union_of(*return_types),
            security=security,
        )

        self.target.client.body.methods.append(model)

    def _mk_params(
        self,
        value: list[openapi.Parameter | openapi.Reference[openapi.Parameter]],
        stack: Stack,
        common_params: Mapping[str, python.MetaField],
    ) -> Iterable[python.MetaField]:
        processed_params = [
            self.process_parameter(oa_param, stack.push(str(idx)))
            for idx, oa_param in enumerate(value)
            if oa_param.name not in common_params
        ]

        all_fields = {field.name: field for field in itertools.chain(common_params.values(), processed_params)}.values()

        direct_fields = []
        metadata_fields = []
        for field in all_fields:
            if field.annotation in ('Cookie', 'Header'):
                metadata_fields.append(field)
            else:
                direct_fields.append(field)
        if metadata_fields:
            metadata = self._mk_response_metafields_metamodel(metadata_fields, stack)
            required = any(field.required for field in metadata_fields)
            direct_fields.append(
                python.MetaField(
                    name='meta',
                    alias=None,
                    type=metadata if required else type_hint.optional(metadata),
                    required=required,
                    annotation='Metadata',
                    style=None,
                )
            )

        return direct_fields

    def _mk_response_metafields_metamodel(self, value: Iterable[python.MetaField], stack: Stack) -> python.TypeHint:
        fields = [field for field in value if field.annotation in ('Cookie', 'Header')]
        metadata_model = python.MetadataModel('RequestMetadata', fields)
        typ = resolve_type_hint(str(self.root_package), stack.push('meta', 'RequestMetadata'))
        self.target.model_modules.append(
            python.MetadataModule(
                path=python.ModulePath(typ.module, is_module=True),
                body=[metadata_model],
            )
        )
        return typ

    def process_global_security(self, value: Iterable[openapi.SecurityRequirement] | None, stack: Stack) -> None:
        self.target.client.body.init_method.security = self.process_security(value, stack)

    def process_security(
        self, value: Iterable[openapi.SecurityRequirement] | None, stack: Stack
    ) -> python.SecurityRequirements | None:
        logger.debug('Process security %s', stack)
        if value is None:
            return None

        return [self.process_security_requirement(item, stack.push(str(idx))) for idx, item in enumerate(value)]

    def process_security_requirement(
        self, value: openapi.SecurityRequirement, stack: Stack
    ) -> Mapping[str, Iterable[str]]:
        logger.debug('Process security requirement %s', stack)
        schemes_root = Stack(('#', 'components', 'securitySchemes'))
        for scheme_name, scopes in value.root.items():
            scheme_stack = schemes_root.push(scheme_name)
            self.process_security_scheme(
                openapi.Reference[openapi.SecuritySchemeBase](ref=str(scheme_stack)), scheme_stack
            )
        return value.root

    # need separate method to resolve references before calling a single-dispatched method
    @resolve_ref
    def process_security_scheme(self, value: openapi.SecuritySchemeBase, stack: Stack) -> None:
        self.process_security_scheme_(value, stack)

    @functools.singledispatchmethod
    def process_security_scheme_(self, _: openapi.SecuritySchemeBase, stack: Stack) -> None:
        raise NotImplementedError(str(stack))

    @process_security_scheme_.register(openapi.APIKeySecurityScheme)
    def _(self, value: openapi.APIKeySecurityScheme, stack: Stack) -> None:
        logger.debug('Process API key security scheme %s', stack)
        auth_name = stack.top()
        flow_name = f'api_key_{auth_name}'
        if flow_name in self.target.security_schemes:
            return

        self.target.security_schemes[flow_name] = python.ApiKeyAuth(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            key=value.name,
            location=value.in_,
            format=value.format,
        )

    @process_security_scheme_.register(openapi.OAuth2SecurityScheme)
    def _(self, value: openapi.OAuth2SecurityScheme, stack: Stack) -> None:
        auth_name = stack.top()
        if auth_name in self.target.security_schemes:
            return

        logger.debug('Process OAuth2 security scheme %s', stack)
        map_process(
            value.flows,
            stack.push('flows'),
            {
                'implicit': self.process_oauth2_implicit,
                'password': self.process_oauth2_password,
                'authorization_code': self.process_oauth2_auth_code,
                'client_credentials': self.process_oauth2_client_credentials,
            },
            True,
        )

    def process_oauth2_implicit(self, value: openapi.ImplicitOAuthFlow, stack: Stack) -> None:
        if value.refresh_url:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_implicit_{auth_name}'] = python.ImplicitOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            authorization_url=value.authorization_url,
            scopes=value.scopes,
        )

    def process_oauth2_password(self, value: openapi.PasswordOAuthFlow, stack: Stack) -> None:
        if value.refresh_url:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_password_{auth_name}'] = python.PasswordOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            token_url=value.token_url,
            scopes=value.scopes,
        )

    def process_oauth2_auth_code(self, value: openapi.AuthorizationCodeOAuthFlow, stack: Stack) -> None:
        if value.refresh_url:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_auth_code_{auth_name}'] = python.AuthorizationCodeOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            authorization_url=value.authorization_url,
            token_url=value.token_url,
            scopes=value.scopes,
        )

    def process_oauth2_client_credentials(self, value: openapi.ClientCredentialsFlow, stack: Stack) -> None:
        if value.refresh_url:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_client_credentials_{auth_name}'] = python.ClientCredentialsOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            token_url=value.token_url,
            scopes=value.scopes,
        )

    @process_security_scheme_.register(openapi.HTTPSecurityScheme)
    def _(self, value: openapi.HTTPSecurityScheme, stack: Stack) -> None:
        logger.debug('Process HTTP security scheme %s', stack)
        auth_name = stack.top()
        flow_name = f'http_{auth_name}'

        if flow_name in self.target.security_schemes:
            return

        try:
            self.target.security_schemes[flow_name] = HTTP_SCHEMES[value.scheme.lower()](
                name=auth_name,
                python_name=names.maybe_mangle_name(auth_name),
            )
        except KeyError:
            raise NotImplementedError(stack.push('scheme'), value.scheme) from None

    def resolve_ref[Target](self, ref: openapi.Reference[Target]) -> tuple[Target, Stack]:
        """Resolve reference to OpenAPI object and its direct path."""
        value, pointer = self.src.resolve_ref(ref)
        return cast(Target, value), Stack.from_str(pointer)


def param_style(
    style: openapi.Style | None,
    explode: bool | None,
    in_: openapi.ParameterLocation,
    stack: Stack,
) -> python.ParamStyle | None:
    if style is explode is None:
        # None = Lapidary uses default
        return None

    if style is None:
        match in_:
            case openapi.ParameterLocation.cookie | openapi.ParameterLocation.query:
                style_name = 'form'
            case openapi.ParameterLocation.header | openapi.ParameterLocation.path:
                style_name = 'simple'
            case _:
                raise ValueError('Unsupported `in`', in_, stack)
    else:
        style_name = style.value

    if explode is None:
        explode = style_name == 'form'

    if style_name == 'simple':
        if in_ == openapi.ParameterLocation.path:
            style_name = 'simple_string'
        else:
            style_name = 'simple_multimap'
    if explode:
        style_name = f'{style_name}_explode'
    try:
        return python.ParamStyle[style_name]
    except ValueError:
        raise ValueError('Unsupported style', style_name, stack)


def parameter_name(value: openapi.Parameter) -> str:
    return value.lapidary_name or names.maybe_mangle_name(value.name) + '_' + value.in_.name[0]


def map_process(
    obj: Any, stack: Stack, processors: Mapping[str, Callable[[Any, Stack], Any]], warn: bool = False
) -> None:
    for key, process in processors.items():
        try:
            if value := getattr(obj, key, None):
                alias = type(obj).model_fields[key].alias
                substack = stack.push(alias or key)
                process(value, substack)
        except NotImplementedError as e:
            if warn:
                logger.warning('Not implemented: %s', e.args[0])
            else:
                raise


HTTP_SCHEMES = {
    'basic': python.HttpBasicAuth,
    'digest': python.HttpDigestAuth,
}
