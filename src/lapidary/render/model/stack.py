from typing import Self


class Stack:
    __slots__ = ('path',)

    def __init__(self, stack=('#',)) -> None:
        self.path: tuple[str, ...] = stack

    @classmethod
    def from_str(cls, pointer: str) -> Self:
        return cls(tuple(pointer.split('/')))

    def __repr__(self):
        return '/'.join(self.path)

    def push(self, *names: str) -> Self:
        return Stack(self.path + names)

    def top(self) -> str:
        return self.path[-1]

    def __hash__(self) -> int:
        return hash(self.path)

    def __eq__(self, other):
        return isinstance(other, Stack) and self.path == other.path

    def __getitem__(self, item: int) -> str:
        return self.path[item]
