from . import openapi, python
from .context import Context
from .python import type_hint_or_union
from .response import process_content
from .stack import Stack


def process_request_body(
    ctx: Context,
    stack: Stack,
    value: openapi.RequestBody,
) -> python.TypeHint | None:
    types = process_content(ctx, stack.push('content'), value.content)
    return type_hint_or_union(types)
