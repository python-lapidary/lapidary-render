import functools
import logging
from collections.abc import Callable, Iterable, Mapping
from typing import Any, cast

from mimeparse import parse_media_range

from lapidary.runtime import SecurityRequirements

from .. import json_pointer, names
from . import openapi, python
from .refs import resolve_ref
from .schema import OpenApi30SchemaConverter
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
        self.global_headers: dict[str, python.Parameter] = {}
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

    def process(self) -> python.ClientModel:
        stack = Stack()

        self.process_servers(self.src.servers, stack.push('servers'))
        self.process_global_responses(self.src.lapidary_responses_global, stack.push('x-lapidary-responses-global'))
        self.process_global_headers(self.src.lapidary_headers_global, stack.push('x-lapidary-headers-global'))
        self.target.client.body.init_method.security = self.process_security(self.src.security, stack.push('security'))
        self.process_paths(self.src.paths, stack.push('paths'))
        self.target.schemas.extend(self.schema_converter.schema_modules)
        return self.target

    def process_servers(self, value: list[openapi.Server] | None, stack: Stack) -> None:
        logger.debug('Process servers %s', stack)

        if not value:
            logger.warning('No servers found')
            return
        if len(value) > 0:
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

    # Not providing process_parameters (plural) as each caller calls it in a different context
    # (list, map or map with defaults)

    @resolve_ref
    def process_parameter(self, value: openapi.Parameter, stack: Stack) -> python.Parameter:
        logger.debug('process_parameter %s', stack)

        if not isinstance(value, openapi.ParameterBase):
            raise TypeError(f'Expected Parameter object at {stack}, got {type(value).__name__}.')
        if value.schema_:
            media_type: str | None = None
            # encoding: str | None = None
            typ = self.schema_converter.process_schema(value.schema_, stack.push('schema'), value.required)
        elif value.content:
            media_type, media_type_obj = next(iter(value.content.items()))
            # encoding = media_type_obj.encoding
            typ = self.schema_converter.process_schema(
                media_type_obj.schema_, stack.push('content', media_type), value.required
            )
        else:
            raise TypeError(f'{stack}: schema or content is required')

        return python.Parameter(
            name=parameter_name(value),
            alias=value.name,
            type=typ,
            in_=value.in_,
            style=value.style,
            explode=value.explode,
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
        common_params = [
            self.process_parameter(param, common_params_stack.push(str(idx)))
            for idx, param in enumerate(value.parameters)
        ]

        for method, operation in value.model_extra.items():
            self.process_operation(operation, stack.push(method), common_params)
        self._path_progress(json_pointer.decode_json_pointer(stack.top()))

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
    ) -> python.MimeMap:
        assert isinstance(value, openapi.Response)
        return self.process_content(value.content, stack.push('content'))

    def process_content(self, value: Mapping[str, openapi.MediaType], stack: Stack) -> python.MimeMap:
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
        common_params: Iterable[python.Parameter],
    ) -> None:
        logger.debug('Process operation %s', stack)

        if not value.operationId:
            raise ValueError(f'{stack}: operationId is required')

        params = self._mk_params(value.parameters, stack.push('parameters'), common_params)

        request_body = (
            self.process_request_body(value.requestBody, stack.push('requestBody')) if value.requestBody else {}
        )
        responses = self.process_responses(value.responses, stack.push('responses'))
        security = self.process_security(value.security, stack.push('security'))

        model = python.OperationFunction(
            name=value.operationId,
            method=stack.top(),
            path=json_pointer.decode_json_pointer(stack[-2]),
            request_body=request_body,
            params=params,
            responses=responses,
            security=security,
        )

        self.target.client.body.methods.append(model)

    def _mk_params(
        self,
        value: list[openapi.Parameter | openapi.Reference[openapi.Parameter]],
        stack: Stack,
        common_params: Iterable[python.Parameter],
    ) -> Iterable[python.Parameter]:
        params = {}
        for param in common_params:
            params[param.name] = param
        for idx, oa_param in enumerate(value):
            param = self.process_parameter(oa_param, stack.push(str(idx)))
            params[param.name] = param
        return list(params.values())

    def process_security(
        self, value: Iterable[openapi.SecurityRequirement] | None, stack: Stack
    ) -> Iterable[SecurityRequirements] | None:
        logger.debug('Process security %s', stack)
        if value is None:
            return None

        security = [self.process_security_requirement(item, stack.push(str(idx))) for idx, item in enumerate(value)]
        return security or None

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
                'authorizationCode': self.process_oauth2_auth_code,
                'clientCredentials': self.process_oauth2_client_credentials,
            },
            True,
        )

    def process_oauth2_implicit(self, value: openapi.ImplicitOAuthFlow, stack: Stack) -> None:
        if value.refreshUrl:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_implicit_{auth_name}'] = python.ImplicitOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            authorization_url=value.authorizationUrl,
            scopes=value.scopes,
        )

    def process_oauth2_password(self, value: openapi.PasswordOAuthFlow, stack: Stack) -> None:
        if value.refreshUrl:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_password_{auth_name}'] = python.PasswordOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            token_url=value.tokenUrl,
            scopes=value.scopes,
        )

    def process_oauth2_auth_code(self, value: openapi.AuthorizationCodeOAuthFlow, stack: Stack) -> None:
        if value.refreshUrl:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_auth_code_{auth_name}'] = python.AuthorizationCodeOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            authorization_url=value.authorizationUrl,
            token_url=value.tokenUrl,
            scopes=value.scopes,
        )

    def process_oauth2_client_credentials(self, value: openapi.ClientCredentialsFlow, stack: Stack) -> None:
        if value.refreshUrl:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_password_{auth_name}'] = python.ClientCredentialsOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            token_url=value.tokenUrl,
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
