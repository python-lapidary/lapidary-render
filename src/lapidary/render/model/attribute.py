from .. import names
from . import openapi, python
from .attribute_annotation import get_attr_annotation
from .context import Context
from .stack import Stack


def process_property(
    ctx: Context,
    stack: Stack,
    value: openapi.Schema | openapi.Reference[openapi.Schema],
    required: bool,
) -> python.AttributeModel:
    alias = value.lapidary_name or names.maybe_mangle_name(stack.top())
    names.check_name(alias, False)

    return python.AttributeModel(
        name=alias,
        annotation=get_attr_annotation(ctx, stack, value, required),
    )
