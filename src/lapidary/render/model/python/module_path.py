import typing
from collections.abc import Iterable
from pathlib import PurePath
from typing import Self


class ModulePath:
    _SEP = '.'

    def __init__(self, module: str | Iterable[str], is_module: bool = True):
        if isinstance(module, str):
            module = module.strip()
            if module.strip() != module:
                raise ValueError(f'"{module}"')
            parts: Iterable[str] = module.split(ModulePath._SEP)
        else:
            parts = module

        if isinstance(parts, list):
            if len(parts) == 0:
                raise ValueError(module)
            self.parts = parts
        else:
            raise ValueError(module)

        self._is_module = is_module

    def to_path(self, root: PurePath | None = None):
        parts = list(self.parts)
        if not self._is_module:
            parts.append('__init__')
        return (root or PurePath()).joinpath(*parts)

    def parent(self) -> typing.Self | None:
        if len(self.parts) == 1:
            return None
        return ModulePath(self.parts[:-1], False)

    def __truediv__(self, other: str | Iterable[str]):
        if isinstance(other, str):
            other = [other]
        return ModulePath([*self.parts, *other])

    def __repr__(self):
        return ModulePath._SEP.join(self.parts)

    def __eq__(self, other: object):
        if not isinstance(other, ModulePath):
            return NotImplemented
        return self.parts == other.parts

    def __hash__(self) -> int:
        return hash(self.__str__())

    def __matmul__(self, other):
        if not isinstance(other, ModulePath):
            return NotImplemented

        if self.parts[: len(other.parts)] != other.parts:
            raise ValueError('Not related')

        return ModulePath(self.parts[len(other.parts) :])
