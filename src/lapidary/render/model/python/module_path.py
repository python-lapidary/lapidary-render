import typing
from collections.abc import Iterable
from pathlib import PurePath


class ModulePath:
    _SEP = '.'

    def __init__(self, module: str | Iterable[str]):
        if isinstance(module, str):
            module = module.strip()
            if module == '' or module.strip() != module:
                raise ValueError()
            parts: Iterable[str] = module.split(ModulePath._SEP)
        else:
            parts = module

        if isinstance(parts, list):
            if len(parts) == 0:
                raise ValueError(module)
            self.parts = parts
        else:
            raise ValueError(module)

    def to_path(self, root: PurePath | None = None, is_module=True):
        path = (root or PurePath()).joinpath(*self.parts)
        if is_module:
            name = self.parts[-1]
            dot_idx = name.rfind('.')
            suffix = name[dot_idx:] if dot_idx != -1 else '.py'
            path = path.with_suffix(suffix)
        return path

    def parent(self) -> typing.Self | None:
        if len(self.parts) == 1:
            return None
        return ModulePath(self.parts[:-1])

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
