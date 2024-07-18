# ignore: F401

import dataclasses as dc
import itertools
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
    ResponseEnvelopeModel,
    ResponseHeader,
    ResponseMap,
    SchemaClass,
    SecurityRequirements,
)
from .module import AbstractModule, AuthModule, ClientModule, EmptyModule, ResponseEnvelopeModule, SchemaModule
from .module_path import ModulePath
from .type_hint import NONE, GenericTypeHint, TypeHint, list_of, union_of


@dc.dataclass
class ClientModel:
    client: ClientModule
    package: str
    schemas: MutableSequence[SchemaModule] = dc.field(default_factory=list)
    security_schemes: MutableMapping[str, Auth] = dc.field(default_factory=dict)
    _response_envelopes: MutableSequence[ResponseEnvelopeModule] = dc.field(default_factory=list)

    def packages(self: Self) -> Iterable[ModulePath]:
        # Used to create __init__.py files in otherwise empty packages

        known_packages: MutableSet[ModulePath] = {ModulePath(self.package)}

        for mod in itertools.chain(self.schemas, self._response_envelopes):
            path: ModulePath | None = mod.path
            while path := path.parent():
                if path in known_packages:
                    break
                yield path
                known_packages.add(path)

    @cached_property
    def modules(self) -> Sequence[AbstractModule]:
        return list(self._modules())

    def _modules(self) -> Iterable[AbstractModule]:
        known_modules = set()
        for mod in itertools.chain(self.schemas, self._response_envelopes):
            assert mod.path not in known_modules, mod.path
            known_modules.add(mod.path)
            yield mod

        for package in self.packages():
            if package not in known_modules:
                yield EmptyModule(path=package, body=None)

    def add_response_envelope_module(self, mod: ResponseEnvelopeModule):
        self._response_envelopes.append(mod)
