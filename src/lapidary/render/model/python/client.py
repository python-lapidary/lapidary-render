import dataclasses
from collections.abc import Mapping

from ..openapi import model as openapi
from ..refs import ResolverFunc
from .client_init import ClientInit, get_client_init
from .module_path import ModulePath
from .op import OperationModel, get_operation_functions


@dataclasses.dataclass(frozen=True)
class ClientModel:
    init_method: ClientInit
    methods: Mapping[str, OperationModel] = dataclasses.field(default_factory=dict)


def get_client_model(openapi_model: openapi.OpenApiModel, module: ModulePath, resolve: ResolverFunc) -> ClientModel:
    return ClientModel(
        init_method=get_client_init(
            openapi_model,
            module,
        ),
        methods=get_operation_functions(openapi_model, module, resolve),
    )
