from __future__ import annotations

import functools
import logging
import typing
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Concatenate

import pydantic
from openapi_pydantic.v3 import v3_0 as openapi

from ..json_pointer import decode_json_pointer
from .stack import Stack

logger = logging.getLogger(__name__)


class HasSource(typing.Protocol):
    source: openapi.OpenAPI


def resolve_ref[Target, R, **P](
    fn: Callable[Concatenate[Any, Target, Stack, P], R],
) -> Callable[Concatenate[Any, Target | openapi.Reference[Target], Stack, P], R]:
    @functools.wraps(fn)
    def wrapper(
        self: HasSource,
        value: Target | openapi.Reference[Target],
        stack: Stack,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        if isinstance(value, openapi.Reference):
            logger.debug('Resolving ref %s', value.ref)
            value, stack_str = resolve_refs_recursive(self.source, value)
            stack = Stack.from_str(stack_str)
        return fn(self, value, stack, *args, **kwargs)

    return wrapper


def resolve_refs_recursive[Target](root: openapi.OpenAPI, ref: openapi.Reference[Target]) -> tuple[Target, str]:
    stack: list[str] = []
    while True:
        pointer = ref.ref
        if pointer in stack:
            raise ValueError('Circular references', stack, pointer)
        stack.append(pointer)
        target = _resolve_ref(root, pointer)
        if not isinstance(target, openapi.Reference):
            return typing.cast(Target, target), ref.ref
        ref = target


def _resolve_ref[Target](obj: typing.Any, ref_str: str) -> Target | openapi.Reference[Target]:
    """Resolve ref without recursion"""

    for name in ref_str.split('/')[1:]:
        name = decode_json_pointer(name)
        obj = _resolve_name(obj, name)
    return obj


def _resolve_name(src: typing.Any, name: str) -> typing.Any:
    if isinstance(src, Sequence):
        return src[int(name)]
    elif isinstance(src, Mapping):
        return src[name]
    else:
        if hasattr(src, name):
            return getattr(src, name)
        for field_name, field_info in typing.cast(pydantic.BaseModel, src).model_fields.items():
            if name == field_info.alias:
                return getattr(src, field_name)
        else:
            raise AttributeError(name)
