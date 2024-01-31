from collections.abc import Iterable
import dataclasses as dc

from . import ResolverFunc
from .client_module import ClientModule, get_client_class_module
from .openapi import OpenApiModel
from .python.module_path import ModulePath
from .schema_module import SchemaModule, get_schema_modules


@dc.dataclass
class ClientModel:
    client: ClientModule
    package: str
    schemas: Iterable[SchemaModule]


def mk_client_model(src: OpenApiModel, root: ModulePath, resolver: ResolverFunc) -> ClientModel:
    return ClientModel(
        client=get_client_class_module(src, root / 'client', root, resolver),
        package=str(root),
        schemas=(list(get_schema_modules(src, root, resolver))),
    )
