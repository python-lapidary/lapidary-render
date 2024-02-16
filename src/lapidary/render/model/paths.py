from . import openapi
from .context import Context
from .operation_function import process_operation
from .params import process_parameter
from .stack import Stack


def process_paths(ctx: Context, stack: Stack, value: openapi.Paths) -> None:
    for path, path_item in value.paths.items():
        path_stack = stack.push(path)
        common_params_stack = path_stack.push('parameters')
        common_params = [
            process_parameter(ctx, common_params_stack.push(idx), param)
            for idx, param in enumerate(path_item.parameters)
        ]

        for method, operation in path_item.model_extra.items():
            process_operation(ctx, path_stack.push(method), operation, common_params)
