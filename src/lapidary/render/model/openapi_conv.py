import logging
from collections.abc import Iterable, Mapping
from typing import cast

from mimeparse import parse_media_range

from .. import names
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
        schema_converter: OpenApi30SchemaConverter | None = None,
    ):
        self.root_package = root_package
        self.global_headers: dict[str, python.Parameter] = {}
        self.src = source

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
        self.process_paths(self.src.paths, stack.push('paths'))
        self.target.schemas.extend(self.schema_converter.schema_modules)
        return self.target

    def process_servers(self, value: list[openapi.Server], stack: Stack) -> None:
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

        self.target.client.body.init_method.base_url = server_url

    def process_global_headers(self, value: Mapping[str, openapi.Header], stack: Stack) -> None:
        logger.debug('Process global headers %s', stack)
        if not value:
            return

        for header_name, header in value.items():
            self.global_headers[header_name] = self.process_parameter(header, stack.push(header_name))

    def process_global_responses(self, value: openapi.Responses, stack: Stack) -> None:
        logger.debug('Process global responses %s', stack)
        if not value:
            return

        self.global_responses = {
            self.process_response(response, stack.push(code)) for code, response in value.responses.items()
        }

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
                media_type_obj.schema_, stack.push_all('content', media_type), value.required
            )
        else:
            raise TypeError(f'{stack}: schema or content is required')

        return python.Parameter(
            name=value.lapidary_name or names.get_param_python_name(value),
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
            path_stack = stack.push(path)
            common_params_stack = path_stack.push('parameters')
            common_params = [
                self.process_parameter(param, common_params_stack.push(idx))
                for idx, param in enumerate(path_item.parameters)
            ]

            for method, operation in path_item.model_extra.items():
                self.process_operation(operation, path_stack.push(method), common_params)

    def process_request_body(self, value: openapi.RequestBody, stack: Stack) -> python.MimeMap:
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
            types[mime] = self.schema_converter.process_schema(media_type.schema_, stack.push_all(mime, 'schema'))
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
            self.process_request_body(value.requestBody, stack.push('requestBody')) if value.requestBody else None
        )
        responses = self.process_responses(value.responses, stack.push('responses'))

        model = python.OperationFunction(
            name=value.operationId,
            method=stack.top(),
            path=stack[-2],
            request_body=request_body,
            params=params,
            responses=responses,
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
            param = self.process_parameter(oa_param, stack.push(idx))
            params[param.name] = param
        return list(params.values())

    def resolve_ref[Target](self, ref: openapi.Reference[Target]) -> tuple[Target, Stack]:
        """Resolve reference to OpenAPI object and its direct path."""
        value, pointer = self.src.resolve_ref(ref)
        return cast(Target, value), Stack.from_str(pointer)
