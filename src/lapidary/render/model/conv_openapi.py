import itertools
import logging
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, MutableMapping, Sequence
from typing import Any

from mimeparse import parse_media_range

from .. import json_pointer, names
from . import metamodel, openapi, python
from .conv_schema import OpenApi30SchemaConverter
from .metamodel import MetaModel, resolve_type_name
from .python import type_hint
from .refs import resolve_ref
from .stack import Stack

logger = logging.getLogger(__name__)


class OpenApi30Converter:
    def __init__(
        self,
        root_package: python.ModulePath,
        source: openapi.OpenAPI,
        origin: str | None,
        path_progress: Callable[[Any], None] | None = None,
    ):
        self.root_package = root_package
        self.global_headers: dict[str, python.Parameter] = {}
        self.global_responses: dict[python.ResponseCode, python.Response]
        self.source = source
        self._origin = origin
        self._path_progress = path_progress

        self.target = python.ClientModel(
            client=python.ClientModule(
                path=python.ModulePath((str(self.root_package), 'client')),
                body=python.ClientClass(init_method=python.ClientInit()),
            ),
            package=str(root_package),
        )

        self._response_cache: MutableMapping[Stack, python.Response] = {}

        self._models: MutableMapping[Stack, metamodel.MetaModel] = {}
        """
        Store all models directly referred by methods.
        Indirectly referred must be accessible via the direct models.
        """

    def process(self) -> python.ClientModel:
        stack = Stack()

        map_process(
            self.source,
            stack,
            {
                'servers': self.process_servers,
                'lapidary_responses_global': self.process_global_responses,
                'lapidary_headers_global': self.process_global_headers,
                'security': self.process_global_security,
                'paths': self.process_paths,
            },
        )

        models: MutableMapping[Stack, python.SchemaClass] = {}
        for model in self._models.values():
            self._collect_schema_models(model, models)

        modules: Mapping[python.ModulePath, list[python.SchemaClass]] = defaultdict(list)
        for stack, class_ in models.items():
            modules[python.ModulePath(resolve_type_name(str(self.root_package), stack).typ.module)].append(class_)

        self.target.model_modules.extend(
            (
                python.SchemaModule(
                    path=module_path,
                    body=models,
                )
                for module_path, models in modules.items()
            )
        )

        return self.target

    def _collect_schema_models(
        self, model: metamodel.MetaModel, models: MutableMapping[Stack, python.SchemaClass]
    ) -> None:
        try:
            if class_ := model.as_type(str(self.root_package)):
                models[model.stack] = class_
        except Exception:
            raise
        for submodel in model.dependencies():
            self._collect_schema_models(submodel, models)

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
    ) -> tuple[python.AnnotatedType, str | None]:
        if value.param_schema and value.content:
            raise ValueError()
        if value.param_schema:
            model = self._process_schema(value.param_schema, stack.push('schema'))
            assert model
            return model.as_annotation(str(self.root_package), value.required), None
        elif value.content:
            media_type, media_type_obj = next(iter(value.content.items()))
            # encoding = media_type_obj.encoding
            model = self._process_schema(
                media_type_obj.media_type_schema or openapi.Schema(), stack.push('content', media_type)
            )
            assert model
            return model.as_annotation(str(self.root_package), value.required), media_type
        else:
            raise TypeError(f'{stack}: schema or content is required')

    # Not providing process_parameters (plural) as each caller calls it in a different context
    # (list, map or map with defaults)

    @resolve_ref
    def process_parameter(self, value: openapi.Parameter, stack: Stack) -> python.Parameter:
        logger.debug('process_parameter %s', stack)

        if not isinstance(value, openapi.ParameterBase):
            raise TypeError(f'Expected Parameter object at {stack}, got {type(value).__name__}.')

        typ, media_type = self._process_schema_or_content(value, stack)
        python_name = parameter_name(value)
        return python.Parameter(
            name=python_name,
            typ=typ,
            in_=value.param_in.value.capitalize(),  # type: ignore[arg-type]
            style=param_style(value.style, value.explode, value.param_in, stack),
            required=value.required,
            media_type=media_type,
            alias=value.name if value.name != python_name else None,
        )

    def process_paths(self, value: openapi.Paths, stack: Stack) -> None:
        for path, path_item in value.paths.items():
            if path.startswith('/'):
                self.process_path(path_item, stack.push(path))

    def process_path(
        self,
        value: openapi.PathItem,
        stack: Stack,
    ) -> None:
        common_params_stack = stack.push('parameters')
        common_params = (
            {
                param.name: self.process_parameter(param, common_params_stack.push(str(idx)))
                for idx, param in enumerate(value.parameters)
            }
            if value.parameters
            else {}
        )

        for method in ('get', 'post', 'put', 'delete', 'head', 'patch', 'options', 'trace'):
            if operation := getattr(value, method):
                self.process_operation(operation, stack.push(method), common_params)
        if self._path_progress:
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

    def process_headers(self, value: Mapping[str, openapi.Header], stack: Stack) -> python.AnnotatedType:
        if not value:
            return python.NoneMetaType
        headers = [self.process_header(header, stack.push(name)) for name, header in value.items()]
        model = python.MetadataModel('ResponseMetadata', headers)
        annotation = resolve_type_name(str(self.root_package), stack.push('ResponseMetadata'))

        self.target.model_modules.append(
            python.MetadataModule(
                path=python.ModulePath(annotation.typ.module, is_module=True),
                body=[model],
            )
        )
        return annotation

    @resolve_ref
    def process_header(self, value: openapi.Header, stack: Stack) -> python.Parameter:
        alias = stack.top()

        typ, _ = self._process_schema_or_content(value, stack)

        python_name = names.maybe_mangle_name(alias)
        return python.Parameter(
            name=python_name,
            typ=typ,
            in_='Header',
            required=value.required,
            style=param_style(value.style, value.explode, openapi.ParameterLocation.HEADER, stack),
            alias=alias if alias != python_name else None,
        )

    def process_content(self, value: Mapping[str, openapi.MediaType], stack: Stack) -> python.MimeMap:
        """Returns: {mime_type: response body type hint}"""
        if not value:
            return {}
        types = {}
        for mime, media_type in value.items():
            mime_parsed = parse_media_range(mime)
            if mime_parsed[:2] != ('application', 'json'):
                continue
            model = self._process_schema(media_type.media_type_schema or openapi.Schema(), stack.push(mime, 'schema'))
            assert model
            types[mime] = model.as_annotation(str(self.root_package))
        return types

    @resolve_ref
    def _process_schema(self, value: openapi.Schema, stack: Stack) -> MetaModel | None:
        if not (model := self._models.get(stack)):
            converter = OpenApi30SchemaConverter(value, stack, self.root_package, self.source)
            if (model := converter.process_schema()) is not None:
                self._models[stack] = model

        return model

    def process_operation(
        self,
        value: openapi.Operation,
        stack: Stack,
        common_params: Mapping[str, python.Parameter],
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

        return_types: set[python.AnnotatedType] = set()
        for status_code, response in responses.items():
            # Don't include error responses in the return type
            if status_code[0] in ('4', '5'):
                continue

            body_type = type_hint.union_of(*response.content.values())
            return_types.add(type_hint.tuple_of(body_type, response.headers_type))

        model = python.OperationFunction(
            name=names.maybe_mangle_name(value.operationId),
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
        value: list[openapi.Parameter | openapi.Reference],
        stack: Stack,
        common_params: Mapping[str, python.Parameter],
    ) -> Sequence[python.Parameter]:
        processed_params: Sequence[python.Parameter] = (
            [self.process_parameter(oa_param, stack.push(str(idx))) for idx, oa_param in enumerate(value)]
            if value
            else ()
        )

        all_fields = {field.name: field for field in itertools.chain(common_params.values(), processed_params)}.values()

        direct_fields = []
        metadata_fields = []
        for field in all_fields:
            if field.in_ in ('Cookie', 'Header'):
                metadata_fields.append(field)
            else:
                direct_fields.append(field)
        if metadata_fields:
            metadata = self._mk_response_metafields_metamodel(metadata_fields, stack)
            required = any(field.required for field in metadata_fields)
            direct_fields.append(
                python.Parameter(
                    name='meta',
                    typ=metadata if required else type_hint.optional(metadata),
                    required=required,
                    in_='Metadata',
                    style=None,
                    alias=None,
                )
            )

        return direct_fields

    def _mk_response_metafields_metamodel(
        self, value: Iterable[python.Parameter], stack: Stack
    ) -> python.AnnotatedType:
        fields = [field for field in value if field.in_ in ('Cookie', 'Header')]
        metadata_model = python.MetadataModel('RequestMetadata', fields)
        typ = resolve_type_name(str(self.root_package), stack.push('meta', 'RequestMetadata'))
        self.target.model_modules.append(
            python.MetadataModule(
                path=python.ModulePath(typ.typ.module, is_module=True),
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
        for scheme_name, scopes in value.items():
            scheme_stack = schemes_root.push(scheme_name)
            self.process_security_scheme(
                openapi.Reference[openapi.SecurityRequirement](ref=str(scheme_stack)), scheme_stack
            )
        return value

    # need separate method to resolve references before calling a single-dispatched method
    @resolve_ref
    def process_security_scheme(self, value: openapi.SecurityScheme, stack: Stack) -> None:
        match value.type:
            case 'apiKey':
                self.process_security_scheme_api_key(value, stack)
            case 'oauth2':
                self.process_security_scheme_oauth2(value, stack)
            case 'http':
                self.process_security_scheme_http(value, stack)

    def process_security_scheme_api_key(self, value: openapi.SecurityScheme, stack: Stack) -> None:
        logger.debug('Process API key security scheme %s', stack)
        auth_name = stack.top()
        flow_name = f'api_key_{auth_name}'
        if flow_name in self.target.security_schemes:
            return

        self.target.security_schemes[flow_name] = python.ApiKeyAuth(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            key=value.name,
            location=openapi.ParameterLocation(value.security_scheme_in),
            format=value.format,
        )

    def process_security_scheme_oauth2(self, value: openapi.SecurityScheme, stack: Stack) -> None:
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

    def process_oauth2_implicit(self, value: openapi.OAuthFlow, stack: Stack) -> None:
        if value.refreshUrl:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_implicit_{auth_name}'] = python.ImplicitOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            authorization_url=value.authorizationUrl,
            scopes=value.scopes,
        )

    def process_oauth2_password(self, value: openapi.OAuthFlow, stack: Stack) -> None:
        if value.refreshUrl:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_password_{auth_name}'] = python.PasswordOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            token_url=value.tokenUrl,
            scopes=value.scopes,
        )

    def process_oauth2_auth_code(self, value: openapi.OAuthFlow, stack: Stack) -> None:
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

    def process_oauth2_client_credentials(self, value: openapi.OAuthFlow, stack: Stack) -> None:
        if value.refreshUrl:
            raise NotImplementedError(stack.push('refreshUrl'))

        auth_name = stack[-3]
        self.target.security_schemes[f'oauth2_client_credentials_{auth_name}'] = python.ClientCredentialsOAuth2Flow(
            name=auth_name,
            python_name=names.maybe_mangle_name(auth_name),
            token_url=value.tokenUrl,
            scopes=value.scopes,
        )

    def process_security_scheme_http(self, value: openapi.SecurityScheme, stack: Stack) -> None:
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


def param_style(
    style: str | None,
    explode: bool | None,
    in_: openapi.ParameterLocation,
    stack: Stack,
) -> python.ParamStyle | None:
    if style is explode is None:
        # None = Lapidary uses default
        return None

    if style is None:
        match in_:
            case 'cookie' | 'query':
                style_name = 'form'
            case 'header' | 'path':
                style_name = 'simple'
            case _:
                raise ValueError('Unsupported `in`', in_, stack)
    else:
        style_name = style

    if explode is None:
        explode = style_name == 'form'

    if style_name == 'simple':
        if in_ == 'path':
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
    return value.lapidary_name or names.maybe_mangle_name(value.name) + '_' + value.param_in.name[0].lower()


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
