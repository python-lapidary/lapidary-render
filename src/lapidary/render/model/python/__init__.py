__all__ = [
    'ApiKeyAuth',
    'Attribute',
    'AttributeAnnotation',
    'Auth',
    'ClientClass',
    'ClientInit',
    'HttpAuth',
    'MimeMap',
    'ModelType',
    'OperationFunction',
    'Parameter',
    'ResponseMap',
    'SchemaClass',
    'AuthModule',
    'ClientModule',
    'SchemaModule',
    'ModulePath',
    'BuiltinTypeHint',
    'GenericTypeHint',
    'TypeHint',
    'type_hint_or_union',
    'ParamLocation',
]

import dataclasses as dc
from collections.abc import Iterable, MutableSequence
from typing import Self

from ..openapi import ParameterLocation as ParamLocation
from .model import (
    ApiKeyAuth,
    Attribute,
    AttributeAnnotation,
    Auth,
    ClientClass,
    ClientInit,
    HttpAuth,
    MimeMap,
    ModelType,
    OperationFunction,
    Parameter,
    ResponseMap,
    SchemaClass,
)
from .module import AuthModule, ClientModule, SchemaModule
from .module_path import ModulePath
from .type_hint import BuiltinTypeHint, GenericTypeHint, TypeHint, type_hint_or_union


@dc.dataclass
class ClientModel:
    client: ClientModule
    package: str
    schemas: MutableSequence[SchemaModule] = dc.field(default_factory=list)

    def packages(self: Self) -> Iterable[ModulePath]:
        # Used to create __init__.py files in otherwise empty packages

        packages = {ModulePath(self.package)}

        # for each schema module get its package
        for schema in self.schemas:
            path = schema.path
            while path := path.parent():
                packages.add(path)

        return packages
