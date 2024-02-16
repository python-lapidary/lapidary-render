import logging

from . import openapi, python
from .attribute_annotation import get_attr_annotation
from .context import Context
from .stack import Stack

logger = logging.getLogger(__name__)


def process_parameter(
    ctx: Context,
    stack: Stack,
    value: openapi.Parameter | openapi.Reference[openapi.Parameter],
) -> python.Parameter:
    logger.debug('process_parameter %s', stack)

    if isinstance(value, openapi.Reference):
        return process_parameter(ctx, *ctx.resolve_stack(value.ref))
    if not isinstance(value, openapi.ParameterBase):
        raise TypeError(f'Expected Parameter object at {stack}, got {type(value).__name__}.')
    if value.schema_:
        return python.Parameter(
            name=value.effective_name,
            annotation=get_attr_annotation(ctx, stack.push('schema'), value.schema_, value.required),
            required=value.required,
            in_=value.in_,
        )
    elif value.content:
        media_type, media_type_obj = next(iter(value.content.items()))

        return python.Parameter(
            name=value.effective_name,
            annotation=get_attr_annotation(
                ctx, stack.push_all('content', media_type), media_type_obj.schema_, value.required
            ),
            required=value.required,
            in_=value.in_,
            media_type=media_type,
        )
    else:
        raise TypeError(f'{stack}: schema or content is required')
