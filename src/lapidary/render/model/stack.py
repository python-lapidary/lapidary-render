from functools import lru_cache
from typing import Any, Self

from ..json_pointer import encode_json_pointer

type Item = tuple[str | int, Any]


class Stack:
    __slots__ = ('path',)

    def __init__(self, stack=('#',)) -> None:
        self.path: tuple[str, ...] = stack

    @classmethod
    def from_str(cls, pointer: str) -> Self:
        return cls(tuple(pointer.split('/')))

    @lru_cache(1)
    def __repr__(self):
        return '/'.join(encode_json_pointer(str(elem)) for elem in self.path)

    def push(self, name: str | int) -> Self:
        return Stack(self.path + (name,))

    def push_all(self, *names: str | int) -> Self:
        return Stack(self.path + names)

    def top(self) -> str:
        return self.path[-1]

    def __hash__(self) -> int:
        return hash(self.path)

    def __eq__(self, other):
        return isinstance(other, Stack) and self.path == other.path
