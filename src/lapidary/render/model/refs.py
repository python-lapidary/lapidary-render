import functools
import logging
from collections.abc import Callable
from typing import Concatenate

from . import openapi
from .stack import Stack

logger = logging.getLogger(__name__)


def resolve_ref[Target, R, **P](
    fn: Callable[Concatenate[Target, Stack, P], R],
) -> Callable[Concatenate[Target | openapi.Reference[Target], Stack, P], R]:
    @functools.wraps(fn)
    def wrapper(self, value: Target | openapi.Reference[Target], stack: Stack, *args) -> R:
        if isinstance(value, openapi.Reference):
            logger.debug('Resolving ref %s', value.ref)
            value, stack = self.resolve_ref(value)
        return fn(self, value, stack, *args)

    return wrapper
