import typing as ty

from lapidary.runtime.http_consts import MIME_JSON
from mimeparse import best_match

from ..names import REQUEST_BODY, escape_name, request_type_name
from . import openapi, python
from .refs import ResolverFunc
from .schema_class import get_schema_classes
from .type_hint import resolve_type_hint


def get_request_body_type(
    op: openapi.Operation,
    module: python.ModulePath,
    resolve: ResolverFunc,
) -> python.TypeHint | None:
    mime_json = best_match(op.requestBody.content.keys(), MIME_JSON)
    if mime_json == '':
        return None
    schema = op.requestBody.content[mime_json].schema_
    return resolve_type_hint(schema, module / REQUEST_BODY / 'content' / escape_name(mime_json), 'schema', resolve)


def get_request_body_classes(
    operation: openapi.Operation,
    module: python.ModulePath,
    resolve: ResolverFunc,
) -> ty.Iterator[python.SchemaClass]:
    rb = operation.requestBody
    if isinstance(rb, openapi.Reference):
        return

    media_map = rb.content
    mime_json = best_match(media_map.keys(), MIME_JSON)
    schema = media_map[mime_json].schema_
    if isinstance(schema, openapi.Reference):
        return

    yield from get_schema_classes(schema, request_type_name(operation.operationId), module, resolve)


def get_request_body_module(
    op: openapi.Operation,
    module: python.ModulePath,
    resolve: ResolverFunc,
) -> python.SchemaModule:
    from .schema_module import _get_schema_module

    classes = [cls for cls in get_request_body_classes(op, module, resolve)]
    return _get_schema_module(classes, module)
