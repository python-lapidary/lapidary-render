import itertools
import logging
import typing
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any, Self

from .. import names
from ..json_pointer import decode_json_pointer, encode_json_pointer
from . import openapi, python
from .stack import Stack

logger = logging.getLogger(__name__)


class Context:
    def __init__(self: Self, oa_model: openapi.OpenApiModel, root_package: str):
        self.source = oa_model
        self.target = python.ClientModel(
            client=python.ClientModule(
                path=python.ModulePath(root_package),
                body=python.ClientClass(init_method=python.ClientInit()),
            ),
            package=root_package,
        )
        self.schema_types: MutableMapping[Stack, python.SchemaClass] = {}
        self.root_package = root_package
        self.global_headers: dict[str, python.Parameter] = {}

    def build_target(self) -> python.ClientModel:
        modules: dict[python.ModulePath, list[python.SchemaClass]] = defaultdict(list)
        for pointer, schema_class in self.schema_types.items():
            hint = self.resolve_type_hint(pointer)
            modules[python.ModulePath(hint.module)].append(schema_class)
        for module, classes in modules.items():
            self.target.schemas.append(
                python.SchemaModule(
                    path=module,
                    body=classes,
                )
            )

        return self.target

    def resolve_ref[Target](self, ref: openapi.Reference[Target]) -> tuple[Stack, Target]:
        """Resolve reference to OpenAPI object and its direct path."""
        pointer, value = self.resolve_ref_str(ref.ref)
        return Stack.from_str(pointer), typing.cast(Target, value)

    def resolve_ref_str(self, pointer: str) -> tuple[str, typing.Any]:
        pointer_in = pointer
        target = _resolve_ref(self.source, pointer)
        stack = [pointer]
        while isinstance(target, openapi.Reference):
            pointer = target.ref
            if pointer in stack:
                raise ValueError('Circular references', stack, pointer)
            else:
                stack.append(pointer)
            target = _resolve_ref(self.source, pointer)
        logger.debug('%s -> %s', pointer_in, pointer)
        return pointer, target

    def resolve_ref2[Target](self, ref: openapi.Reference[Target]) -> tuple[str, Target, python.ModulePath]:
        """Resolve reference to OpenAPI object and its direct path."""
        pass

    def resolve_stack(self, pointer: str) -> tuple[Stack, Any]:
        pointer, value = self.resolve_ref_str(pointer)
        return Stack.from_str(pointer), value

    def resolve_type_hint(self, pointer: str | Stack) -> python.TypeHint:
        if isinstance(pointer, Stack):
            parts = pointer.path[1:]
        else:
            parts = pointer.split('/')[1:]
        module_name = '.'.join(
            itertools.chain(
                (self.root_package,), [names.maybe_mangle_name(encode_json_pointer(part)) for part in parts[:-1]]
            )
        )
        top: str | int = parts[-1]
        if isinstance(top, int):
            top = parts[-2] + str(top)
        return python.TypeHint(module=module_name, name=top)


def _resolve_ref[Target](src: openapi.OpenApiModel, ref_str: str) -> Target | openapi.Reference[Target]:
    """Resolve ref without recursion"""
    obj: typing.Any = src
    for name in ref_str.split('/')[1:]:
        name = decode_json_pointer(name)
        obj = _resolve_name(obj, name)
    return obj


def _resolve_name(src: typing.Any, name: str) -> typing.Any:
    if isinstance(src, openapi.Paths) and name in src.paths:
        src = src.paths
    elif isinstance(src, openapi.PathItem) and name in src.model_extra:
        src = src.model_extra
    if isinstance(src, Sequence):
        src = src[int(name)]
    elif isinstance(src, Mapping):
        src = src[name]
    else:
        src = getattr(src, name)
    return src
