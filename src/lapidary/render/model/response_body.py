from collections.abc import Iterable
import typing as ty

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.module_path import ModulePath

from .schema_class import get_schema_classes
from .schema_class_model import SchemaClass

if ty.TYPE_CHECKING:
    from .schema_module import SchemaModule


def get_response_body_classes(
        operation: openapi.Operation,
        module: ModulePath,
        resolve: ResolverFunc,
) -> Iterable[SchemaClass]:
    for status_code, response in operation.responses.items():
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


def get_response_body_module(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> 'SchemaModule':
    from .schema_module import _get_schema_module
    classes = [cls for cls in get_response_body_classes(op, module, resolve)]
    return _get_schema_module(classes, module)
