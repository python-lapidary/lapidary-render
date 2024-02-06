from .client_module import get_client_class_module
from .openapi import OpenApiModel
from .python import ClientModel, ModulePath
from .refs import ResolverFunc
from .schema_module import get_schema_modules


def mk_client_model(src: OpenApiModel, root: ModulePath, resolver: ResolverFunc) -> ClientModel:
    return ClientModel(
        client=get_client_class_module(src, root / 'client', root, resolver),
        package=str(root),
        schemas=(list(get_schema_modules(src, root, resolver))),
    )
