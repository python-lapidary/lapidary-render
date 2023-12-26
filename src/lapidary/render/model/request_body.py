import typing as ty

from lapidary.runtime import openapi
from lapidary.runtime.http_consts import MIME_JSON
from lapidary.runtime.model import TypeHint, resolve_type_hint
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.names import REQUEST_BODY, escape_name, request_type_name
from mimeparse import best_match

from .schema_class import get_schema_classes
from .schema_class_model import SchemaClass

if ty.TYPE_CHECKING:
    from .schema_module import SchemaModule


def get_request_body_type(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> ty.Optional[TypeHint]:
    mime_json = best_match(op.requestBody.content.keys(), MIME_JSON)
    if mime_json == '':
        return None
    schema = op.requestBody.content[mime_json].schema_
    return resolve_type_hint(schema, module / REQUEST_BODY / "content" / escape_name(mime_json), "schema", resolve)


def get_request_body_classes(
        operation: openapi.Operation,
        module: ModulePath,
        resolve: ResolverFunc,
) -> ty.Iterator[SchemaClass]:
    rb = operation.requestBody
    if isinstance(rb, openapi.Reference):
        return

    media_map = rb.content
    mime_json = best_match(media_map.keys(), MIME_JSON)
    schema = media_map[mime_json].schema_
    if isinstance(schema, openapi.Reference):
        return

    yield from get_schema_classes(schema, request_type_name(operation.operationId), module, resolve)


def get_request_body_module(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> 'SchemaModule':
    from .schema_module import _get_schema_module
    classes = [cls for cls in get_request_body_classes(op, module, resolve)]
    return _get_schema_module(classes, module)
