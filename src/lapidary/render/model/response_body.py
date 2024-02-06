from collections.abc import Iterable

from . import openapi, python
from .refs import ResolverFunc
from .schema_class import get_schema_classes


def get_response_body_classes(
        operation: openapi.Operation,
        module: python.ModulePath,
        resolve: ResolverFunc,
) -> Iterable[python.SchemaClass]:
    for status_code, response in operation.responses.responses.items():
        if isinstance(response, openapi.Reference):
            continue
        if response.content is None:
            continue
        for _media_type_name, media_type in response.content.items():
            schema = media_type.schema_
            if schema is None:
                continue
            if isinstance(schema, openapi.Reference):
                continue
            yield from get_schema_classes(schema, 'Response', module, resolve)


def get_response_body_module(op: openapi.Operation, module: python.ModulePath, resolve: ResolverFunc) -> python.SchemaModule:
    from .schema_module import _get_schema_module
    classes = [cls for cls in get_response_body_classes(op, module, resolve)]
    return _get_schema_module(classes, module)
