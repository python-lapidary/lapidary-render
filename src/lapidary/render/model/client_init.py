import logging
from collections.abc import Mapping

from . import openapi
from .context import Context
from .params import process_parameter
from .response import process_response
from .stack import Stack

logger = logging.getLogger(__name__)


def process_global_headers(ctx: Context, stack: Stack, value: Mapping[str, openapi.Header]) -> None:
    logger.debug('Process global headers %s', stack)
    if not value:
        return

    for header_name, header in value.items():
        ctx.global_headers[header_name] = process_parameter(ctx, stack.push(header_name), header)


def process_global_responses(ctx: Context, stack: Stack, value: openapi.Responses) -> None:
    logger.debug('Process global responses %s', stack)
    if not value:
        return

    ctx.global_responses = {
        process_response(ctx, stack.push(code), response) for code, response in value.responses.items()
    }
