import logging
from collections.abc import Iterable

from .. import names
from . import openapi, python
from .context import Context
from .params import process_parameter
from .request_body import process_request_body
from .response import process_responses
from .stack import Stack

logger = logging.getLogger(__name__)


def process_operation(
    ctx: Context,
    stack: Stack,
    value: openapi.Operation,
    common_params: Iterable[python.Parameter],
) -> None:
    logger.debug('Process operation %s', stack)

    if not value.operationId:
        raise ValueError(f'{stack}: operationId is required')

    params = _mk_params(ctx, stack.push('parameters'), value.parameters, common_params)

    request_type = (
        process_request_body(ctx, stack.push('requestBody'), value.requestBody) if value.requestBody else None
    )
    response_type = process_responses(ctx, stack.push('responses'), value.responses) if value.responses else None

    model = python.OperationFunctionModel(
        name=value.operationId,
        request_type=request_type,
        params=list(params.values()),
        response_type=response_type,
        auth_name=None,
    )

    ctx.target.client.body.methods.append(model)


def _mk_params(
    ctx: Context,
    stack: Stack,
    value: list[openapi.Parameter | openapi.Reference[openapi.Parameter]],
    common_params: Iterable[python.Parameter],
):
    params = {}
    for param in common_params:
        params[names.get_param_python_name(param)] = param
    for idx, oa_param in enumerate(value):
        param = process_parameter(ctx, stack.push(idx), oa_param)
        params[names.get_param_python_name(param)] = param
    return params
