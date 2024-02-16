from . import openapi, python
from .client_init import process_global_headers, process_global_responses
from .context import Context
from .paths import process_paths
from .stack import Stack


def mk_client_model(src: openapi.OpenApiModel, root: python.ModulePath) -> python.ClientModel:
    ctx = Context(src, str(root))

    stack = Stack()
    process_global_responses(ctx, stack.push('x-lapidary-responses-global'), src.lapidary_responses_global)
    process_global_headers(ctx, stack.push('x-lapidary-headers-global'), src.lapidary_headers_global)
    process_paths(ctx, stack.push('paths'), src.paths)

    return ctx.build_target()
