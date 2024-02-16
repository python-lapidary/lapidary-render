import datetime as dt
import logging
import uuid
from typing import TYPE_CHECKING

from lapidary.runtime.absent import Absent

from . import openapi, python
from .stack import Stack

if TYPE_CHECKING:
    from .context import Context

logger = logging.getLogger(__name__)

STRING_FORMATS = {
    'uuid': uuid.UUID,
    'date': dt.date,
    'date-time': dt.datetime,
}

PRIMITIVE_TYPES = {
    openapi.Type.string: str,
    openapi.Type.integer: int,
    openapi.Type.number: float,
    openapi.Type.boolean: bool,
}


def get_type_hint(
    ctx: Context,
    stack: Stack,
    value: openapi.Schema | openapi.Reference[openapi.Schema],
) -> python.TypeHint:
    if isinstance(value, openapi.Reference):
        return get_type_hint(ctx, *ctx.resolve_ref(value))

    typ = _get_type_hint(ctx, stack, value)

    required = True  # TODO

    if value.nullable:
        typ = typ.union_with(python.BuiltinTypeHint.from_str('None'))
    if not required:
        typ = typ.union_with(python.TypeHint.from_type(Absent))

    return typ


def _get_one_of_type_hint(
    ctx: Context,
    stack: Stack,
    schema: openapi.Schema,
) -> python.TypeHint:
    args = []
    for idx, sub_schema in enumerate(schema.oneOf):
        if isinstance(sub_schema, openapi.Reference):
            stack, sub_schema = ctx.resolve_ref(sub_schema)

        type_hint = get_type_hint(ctx, stack.push(idx), sub_schema)
        args.append(type_hint)

    return python.GenericTypeHint(
        module='typing',
        name='Union',
        args=tuple(args),
    )


def _get_composite_type_hint(
    ctx: Context,
    stack: Stack,
    schemas: list[openapi.Schema | openapi.Reference],
) -> python.TypeHint:
    if len(schemas) != 1:
        raise NotImplementedError(stack, 'Multiple component schemas (allOf, anyOf, oneOf) are currently unsupported.')

    return get_type_hint(ctx, stack, schemas[0])


def _get_type_hint(
    ctx: Context,
    stack: Stack,
    value: openapi.Schema,
) -> python.TypeHint:
    if value.type == openapi.Type.string:
        return python.TypeHint.from_type(STRING_FORMATS.get(value.format, str))
    elif value.type in PRIMITIVE_TYPES:
        return python.BuiltinTypeHint.from_str(PRIMITIVE_TYPES[value.type].__name__)
    elif value.type == openapi.Type.object:
        return ctx.resolve_type_hint(stack)
    elif value.type == openapi.Type.array:
        return _get_type_hint_array(ctx, stack.push('items'), value.items)
    elif value.anyOf:
        return _get_one_of_type_hint(ctx, stack, value)
    elif value.oneOf:
        return _get_one_of_type_hint(ctx, stack, value)
    elif value.allOf:
        return _get_composite_type_hint(ctx, stack.push('allOf'), value.allOf)
    elif value.type is None:
        return python.TypeHint.from_str('typing:Any')
    else:
        raise NotImplementedError


def _get_type_hint_array(
    ctx: Context, stack: Stack, value: openapi.Schema | openapi.Reference[openapi.Schema]
) -> python.TypeHint:
    if isinstance(value, openapi.Reference):
        return _get_type_hint_array(ctx, *ctx.resolve_ref(value))

    return get_type_hint(ctx, stack, value).list_of()


def resolve_type_hint(
    ctx: Context, stack: Stack, value: openapi.Schema | openapi.Reference[openapi.Schema]
) -> python.TypeHint:
    if isinstance(value, openapi.Reference):
        return resolve_type_hint(ctx, *ctx.resolve_ref(value))
    return get_type_hint(ctx, stack, value)
