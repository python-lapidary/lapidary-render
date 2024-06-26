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
from collections.abc import Iterable, MutableMapping, MutableSequence, MutableSet, Sequence
from functools import cached_property
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
from .module import AbstractModule, AuthModule, ClientModule, EmptyModule, SchemaModule
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

        known_packages: MutableSet[ModulePath] = {ModulePath.root()}

        # for each schema module get its package
        for schema in self.schemas:
            path: ModulePath | None = schema.path
            while path := path.parent():
                if path in known_packages:
                    continue
                yield path
                known_packages.add(path)

    @cached_property
    def modules(self) -> Sequence[AbstractModule]:
        return list(self._modules())

    def _modules(self) -> Iterable[AbstractModule]:
        yield from self.schemas
        for package in self.packages():
            yield EmptyModule(path=package, body=None)
