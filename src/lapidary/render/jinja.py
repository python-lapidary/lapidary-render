from collections.abc import Mapping
from functools import cached_property
from importlib.metadata import version as get_version
from pathlib import Path
from typing import Any

import jinja2.ext
from lapidary.runtime import openapi
from lapidary.runtime.model import TypeHint, ResolverFunc, get_resolver, resolve_ref
from lapidary.runtime.model.type_hint import BUILTINS
from lapidary.runtime.module_path import ModulePath

from .model import get_client_class_module, AuthModule, get_auth_module
from .model.schema_module import get_schema_module, get_param_model_classes_module

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
        if type_ref is None:
            return "None"
        if isinstance(type_ref, str):
            import builtins
            if type_ref in dir(builtins):
                type_ref = TypeHint(module=BUILTINS, type_name=type_ref)
            else:
                type_ref = TypeHint.from_str(type_ref)
        if isinstance(this_mod, str) and this_mod.startswith("#"):
            _, this_mod, _ = self._resolver(openapi.Reference(ref=this_mod))
        if isinstance(this_mod, ModulePath):
            this_mod = str(this_mod)
        return type_ref.to_str(this_mod)

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
        if path.startswith("#/paths/") and path.endswith("/parameters"):
            op = resolve_ref(self.model, path[:-11], openapi.Operation)
            return get_param_model_classes_module(op, ModulePath.from_reference(self._root, path, self.model), self._resolver)
        return get_schema_module(
            resolve_ref(self.model, path),
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
