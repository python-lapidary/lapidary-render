from dataclasses import dataclass, field

from . import openapi
from .client_init import ClientInit, get_client_init
from .openapi.utils import get_operations
from .operation_function import OperationFunctionModel, get_operation_func
from .python import ModulePath
from .python.names import get_ops_module
from .refs import ResolverFunc


@dataclass(frozen=True)
class ClientClass:
    init_method: ClientInit
    methods: list[OperationFunctionModel] = field(default_factory=list)


def get_client_class(openapi_model: openapi.OpenApiModel, root_module: ModulePath, resolver: ResolverFunc) -> ClientClass:
    functions = [
        get_operation_func(op, get_ops_module(root_module), resolver)
        for url_path, path_item in openapi_model.paths.model_extra.items()
        for method, op in get_operations(path_item, True)
    ]

    return ClientClass(
        init_method=get_client_init(openapi_model, root_module, resolver),
        methods=functions,
    )
