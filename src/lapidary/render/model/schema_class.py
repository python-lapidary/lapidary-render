import logging

from . import openapi, python
from .attribute import process_property
from .context import Context
from .openapi import Schema
from .stack import Stack
from .type_hint import get_type_hint

logger = logging.getLogger(__name__)


def process_schema(
    ctx: Context,
    stack: Stack,
    value: Schema,
) -> python.TypeHint:
    logger.debug('process schema %s', stack)

    if isinstance(value, openapi.Reference):
        return process_schema(ctx, *ctx.resolve_ref(value))

    assert isinstance(value, openapi.Schema)

    name = value.lapidary_name or stack.top()

    path = str(stack)
    if path not in ctx.schema_types:
        base_type = (
            python.TypeHint.from_type(Exception)
            if value.lapidary_model_type is openapi.LapidaryModelType.exception
            else python.TypeHint.from_str('pydantic:BaseModel')
        )

        stack_attr = stack.push('properties')
        attributes = [
            process_property(ctx, stack_attr.push(prop_name), prop_schema, prop_name in value.required)
            for prop_name, prop_schema in value.properties.items()
        ]

        ctx.schema_types[stack] = python.SchemaClass(
            class_name=name,
            base_type=base_type,
            allow_extra=value.additionalProperties is not False,
            has_aliases=any(['alias' in attr.annotation.field_props for attr in attributes]),
            attributes=attributes,
            docstr=value.description or None,
            model_type=python.ModelType[value.lapidary_model_type.name]
            if value.lapidary_model_type
            else python.ModelType.model,
        )

    return get_type_hint(ctx, stack, value)
