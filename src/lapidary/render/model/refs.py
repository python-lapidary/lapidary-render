from __future__ import annotations

import functools
import logging
import typing
from collections.abc import Callable
from typing import Any, Concatenate

from . import openapi
from .stack import Stack

logger = logging.getLogger(__name__)


class SupportsResolveRef[Target](typing.Protocol):
    def resolve_ref(self: typing.Self, ref: openapi.Reference[Target]) -> tuple[Target, Stack]:
        pass


def resolve_ref[Target, R, **P](
    fn: Callable[Concatenate[Any, Target, Stack, P], R],
) -> Callable[Concatenate[Any, Target | openapi.Reference[Target], Stack, P], R]:
    @functools.wraps(fn)
    def wrapper(
        self: SupportsResolveRef,
        value: Target | openapi.Reference[Target],
        stack: Stack,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        if isinstance(value, openapi.Reference):
            logger.debug('Resolving ref %s', value.ref)
            value, stack = self.resolve_ref(value)
        return fn(self, value, stack, *args, **kwargs)

    return wrapper
