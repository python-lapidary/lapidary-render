from collections.abc import Collection, Iterable, Mapping

from mimeparse import parse_media_range

from . import openapi, python
from .context import Context
from .schema_class import process_schema
from .stack import Stack


def process_responses(ctx: Context, stack: Stack, value: openapi.Responses) -> python.TypeHint:
    types = {
        typ for code, response in value.responses.items() for typ in process_response(ctx, stack.push(code), response)
    }

    return python.type_hint_or_union(types)


def process_response(
    ctx: Context, stack: Stack, value: openapi.Response | openapi.Reference[openapi.Response]
) -> Iterable[python.TypeHint]:
    if isinstance(value, openapi.Reference):
        return process_response(ctx, *ctx.resolve_ref(value))

    return process_content(ctx, stack.push('content'), value.content)


def process_content(ctx: Context, stack: Stack, self: Mapping[str, openapi.MediaType]) -> Collection[python.TypeHint]:
    types = set()
    for mime, media_type in self.items():
        mime_parsed = parse_media_range(mime)
        if mime_parsed[:2] != ('application', 'json'):
            continue
        types.add(process_schema(ctx, stack.push_all(mime, 'schema'), media_type.schema_))
    return types
