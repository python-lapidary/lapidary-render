import logging
import typing

from .json_pointer import encode_json_pointer
from .model import openapi
from .model.refs import resolve_ref

logger = logging.getLogger(__name__)
Document: typing.TypeAlias = typing.Mapping[str, typing.Any]
T = typing.TypeVar('T')


def extract_items(model: openapi.OpenApiModel) -> typing.Iterable[str]:
    extractor = _ItemListExtractor(model)
    extractor.extract()
    return extractor.known


class _ItemListExtractor:
    def __init__(self, model: openapi.OpenApiModel):
        self.model = model
        self.known = set()

    def extract(self) -> None:
        self._process_operations()

    def _process_operations(self) -> None:
        for path, path_item in self.model.paths.items():
            for method, operation in openapi.get_operations(path_item):
                self._process_model_or_ref(operation, f"#/paths/{encode_json_pointer(path)}/{method}", self._process_operation)

    def _process_model_or_ref(self, model_or_ref: T | openapi.Reference, path: str, process_model: typing.Callable[[T, str], None]) -> None:
        if isinstance(model_or_ref, openapi.Reference):
            path = model_or_ref.ref
            model = resolve_ref(self.model, path)
        else:
            model = model_or_ref

        process_model(model, path)

    def _process_operation(self, operation: openapi.Operation, path: str) -> None:
        if operation.parameters:
            for parameter_or_ref in operation.parameters:
                self._process_model_or_ref(parameter_or_ref, path, self._process_parameter)

        if operation.requestBody:
            self._process_model_or_ref(operation.requestBody, path + "/requestBody", self._process_request_body)

        for response_code, response_or_ref in operation.responses.responses.items():
            self._process_model_or_ref(response_or_ref, f"{path}/responses/{str(response_code)}", self._process_response)

    def _process_parameter(self, parameter: openapi.Parameter, path: str) -> None:
        """Child schemas yield a single item "$path/parameters", references yield separate items each"""
        if parameter.schema_:
            if isinstance(parameter.schema_, openapi.Reference):
                self._process_schema_or_ref(parameter.schema_, path + "/parameters")
            else:
                self._collect_and_continue(path + "/parameters")

    def _process_response(self, response: openapi.Response, path: str) -> None:
        if response.content:
            for mime_type, media_type in response.content.items():
                self._process_schema_or_ref(media_type.schema_, f"{path}/content/{encode_json_pointer(mime_type)}/schema")

    def _process_request_body(self, request_body: openapi.RequestBody, path: str) -> None:
        if request_body.content:
            for mime_type, media_type in request_body.content.items():
                self._process_schema_or_ref(media_type.schema_, f"{path}/content/{encode_json_pointer(mime_type)}/schema")

    def _process_schema_or_ref(self, model: openapi.Schema | openapi.Reference, path: str) -> None:
        """Only references to object schemas produce item. This applies recursively to their properties."""

        if isinstance(model, openapi.Reference):
            path = model.ref
            schema = resolve_ref(self.model, path, openapi.Schema)
            self._process_schema(schema, path)
        else:
            if self._collect_and_continue(path):
                self._process_schema(model, path)

    def _process_schema(self, schema: openapi.Schema, path: str) -> None:
        if schema.type == openapi.Type.object:
            if self._collect_and_continue(path) and schema.properties:
                for name, property_or_ref in schema.properties.items():
                    if isinstance(property_or_ref, openapi.Reference):
                        self._process_model_or_ref(property_or_ref, path + '/' + name, self._process_schema_or_ref)

    def _collect_and_continue(self, path: str) -> bool:
        continue_ = path in self.known
        self.known.add(path)
        return continue_
