from ..names import get_paths_module
from . import openapi, python
from .client_init import get_client_init
from .openapi.utils import get_operations
from .operation_function import get_operation_func
from .refs import ResolverFunc


def get_client_class(
    openapi_model: openapi.OpenApiModel,
    root_module: python.ModulePath,
    resolver: ResolverFunc,
) -> python.ClientClass:
    functions = [
        get_operation_func(op, get_paths_module(root_module), resolver)
        for _, path_item in openapi_model.paths.paths.items()
        for _, op in get_operations(path_item, True)
    ]

    return python.ClientClass(
        init_method=get_client_init(openapi_model, root_module),
        methods=functions,
    )
