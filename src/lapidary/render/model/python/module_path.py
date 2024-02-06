from __future__ import annotations

import pathlib
import typing
from collections.abc import Iterable


class ModulePath:
    _SEP = '.'

    def __init__(self, module: str | Iterable[str]):
        if isinstance(module, str):
            module = module.strip()
            if module == '' or module.strip() != module:
                raise ValueError()
            parts = module.split(ModulePath._SEP)
        else:
            parts = module

        if isinstance(parts, list):
            if len(parts) == 0:
                raise ValueError(module)
            self.parts = parts
        else:
            raise ValueError(module)

    def to_path(self, root: pathlib.Path, is_module=True):
        path = root.joinpath(*self.parts)
        if is_module:
            name = self.parts[-1]
            dot_idx = name.rfind('.')
            suffix = name[dot_idx:] if dot_idx != -1 else '.py'
            path = path.with_suffix(suffix)
        return path

    def parent(self) -> typing.Self:
        return ModulePath(self.parts[:-1])

    def __truediv__(self, other: str | Iterable[__str__]):
        if isinstance(other, str):
            other = [other]
        return ModulePath([*self.parts, *other])

    def __str__(self):
        return ModulePath._SEP.join(self.parts)

    def __eq__(self, other: typing.Self):
        return self.parts == other.parts
