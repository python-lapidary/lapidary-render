__all__ = (
    'Annotation',
    'ApiKeyAuth',
    'Auth',
    'AuthModule',
    'AuthorizationCodeOAuth2Flow',
    'BuiltinTypeHint',
    'ClientClass',
    'ClientCredentialsOAuth2Flow',
    'ClientInit',
    'ClientModule',
    'Field',
    'GenericTypeHint',
    'HttpBasicAuth',
    'HttpDigestAuth',
    'ImplicitOAuth2Flow',
    'MimeMap',
    'ModelType',
    'ModulePath',
    'NONE',
    'OperationFunction',
    'ParamLocation',
    'Parameter',
    'PasswordOAuth2Flow',
    'ResponseMap',
    'SchemaClass',
    'SchemaModule',
    'SecurityRequirements',
    'TypeHint',
    'type_hint_or_union',
)

import dataclasses as dc
from collections.abc import Iterable, MutableMapping, MutableSequence
from typing import Self

from ..openapi import ParameterLocation as ParamLocation
from .model import (
    Annotation,
    ApiKeyAuth,
    Auth,
    AuthorizationCodeOAuth2Flow,
    ClientClass,
    ClientCredentialsOAuth2Flow,
    ClientInit,
    Field,
    HttpBasicAuth,
    HttpDigestAuth,
    ImplicitOAuth2Flow,
    MimeMap,
    ModelType,
    OperationFunction,
    Parameter,
    PasswordOAuth2Flow,
    ResponseMap,
    SchemaClass,
    SecurityRequirements,
)
from .module import AuthModule, ClientModule, SchemaModule
from .module_path import ModulePath
from .type_hint import NONE, BuiltinTypeHint, GenericTypeHint, TypeHint, type_hint_or_union


@dc.dataclass
class ClientModel:
    client: ClientModule
    package: str
    schemas: MutableSequence[SchemaModule] = dc.field(default_factory=list)
    security_schemes: MutableMapping[str, Auth] = dc.field(default_factory=dict)

    def packages(self: Self) -> Iterable[ModulePath]:
        # Used to create __init__.py files in otherwise empty packages

        packages = {ModulePath(self.package)}

        # for each schema module get its package
        for schema in self.schemas:
            path = schema.path
            while path_ := path.parent():
                packages.add(path_)
                path = path_

        return packages
