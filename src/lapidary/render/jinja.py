from collections.abc import Mapping
from functools import cached_property
from pathlib import Path
from typing import Any

import jinja2.ext
from lapidary.runtime import openapi
from lapidary.runtime.model import TypeHint, ResolverFunc, get_resolver
from lapidary.runtime.model.refs import _schema_get, resolve
from lapidary.runtime.model.type_hint import BuiltinTypeHint
from lapidary.runtime.module_path import ModulePath

from lapidary.render.model import get_client_class_module, AuthModule, get_auth_module
from lapidary.render.model.schema_module import get_schema_module
from importlib.metadata import version as get_version

document: Mapping[str: Any]
package: str
model: openapi.OpenApiModel
"""Hack: allow Lapidary main and Jinja extension share the model.
Jinja discourages passing variables on the side, but it should be safe in our case"""

"""Extension allowing to modify the Copier context."""


class LapidaryModel:
    get_version = staticmethod(get_version)
    version = get_version  # compat

    @cached_property
    def document(self) -> Mapping:
        return document

    @cached_property
    def model(self) -> openapi.OpenApiModel:
        return model

    def resolve_module(self, path: str) -> str:
        from lapidary.runtime.module_path import ModulePath

        return str(ModulePath.from_reference(self._root, path, self.model).to_path(Path('.'), False))

    def type_hint(self, type_ref: TypeHint | str, this_mod: ModulePath | str) -> str:
        if isinstance(type_ref, str):
            import builtins
            if type_ref in dir(builtins):
                type_ref = BuiltinTypeHint(name=type_ref)
            else:
                type_ref = TypeHint.from_str(type_ref)
        if isinstance(this_mod, str) and this_mod.startswith("#"):
            _, this_mod, _ = self._resolver(openapi.Reference(ref=this_mod), openapi.Schema)
        if isinstance(this_mod, ModulePath):
            this_mod = str(this_mod)
        return type_ref.full_name(this_mod)

    @property
    def _root(self) -> ModulePath:
        return ModulePath(package)

    @property
    def auth_model(self) -> AuthModule:
        return get_auth_module(model, self._root / "auth")

    @property
    def client_model(self):
        return get_client_class_module(model, self._root / "client", self._root, self._resolver)

    def schema_model(self, path: str):
        return get_schema_module(
            _schema_get(self.model, path, openapi.Schema),
            path.split('/')[-1],
            ModulePath.from_reference(self._root, path, self.model),
            self._resolver,
        )

    @cached_property
    def _resolver(self) -> ResolverFunc:
        return get_resolver(self.model, package)


class LapidaryExtension(jinja2.ext.Extension):
    def __init__(self, env: jinja2.Environment):
        super().__init__(env)

        env.filters["as_module_path"] = ModulePath
        env.globals.update(dict(
            document=document,
            lapidary=LapidaryModel()
        ))
