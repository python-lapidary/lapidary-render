import re
from typing import Self

from .. import json_pointer

RE_SPECIAL = re.compile('/|~(?!0)')


class Stack:
    # store parts unescaped, only escape when printing

    __slots__ = ('path',)

    def __init__(self, stack=('#',)) -> None:
        self.path: tuple[str, ...] = stack

    @classmethod
    def from_str(cls, pointer: str) -> Self:
        return cls(tuple([json_pointer.decode_json_pointer(part) for part in pointer.split('/')]))

    def __repr__(self):
        return '/'.join((self.path[0], *[json_pointer.encode_json_pointer(elem) for elem in self.path[1:]]))

    def push(self, *names: str) -> Self:
        return Stack(self.path + names)  # type: ignore[return-value]

    def top(self) -> str:
        return self.path[-1]

    def __hash__(self) -> int:
        return hash(self.path)

    def __eq__(self, other):
        return isinstance(other, Stack) and self.path == other.path

    def __getitem__(self, item: int) -> str:
        return self.path[item]
