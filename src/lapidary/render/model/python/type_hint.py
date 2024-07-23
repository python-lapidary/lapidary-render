import dataclasses as dc
from collections.abc import Iterable, MutableSet
from typing import Self, cast


@dc.dataclass(slots=True, frozen=True, kw_only=True)
class TypeHint:
    module: str
    name: str

    def __repr__(self):
        return self.full_name()

    def full_name(self):
        return self.module + ':' + self.name if self.module != 'builtins' else self.name

    @staticmethod
    def from_str(path: str) -> 'TypeHint':
        module, name = path.split(':')
        return TypeHint(module=module, name=name)

    @staticmethod
    def from_type(typ: type) -> 'TypeHint':
        if hasattr(typ, '__origin__'):
            raise ValueError('Generic types unsupported', typ)
        module = typ.__module__
        name = typ.__name__
        return TypeHint(module=module, name=name)

    def imports(self) -> Iterable[str]:
        return [self.module]

    def is_union(self) -> bool:
        return False

    # used by template
    def is_none(self) -> bool:
        return False

    def get_origin(self) -> Self:
        return self

    def get_args(self) -> Iterable[Self]:
        return ()

    def __eq__(self, other) -> bool:
        return isinstance(other, TypeHint) and self.module == other.module and self.name == other.name

    def __hash__(self) -> int:
        return self.module.__hash__() * 14159 + self.name.__hash__()


@dc.dataclass(slots=True, frozen=True, kw_only=True)
class GenericTypeHint(TypeHint):
    args: Iterable[TypeHint]

    def is_union(self) -> bool:
        return self.module == 'typing' and self.name == 'Union'

    def get_origin(self) -> Self:
        return TypeHint(module=self.module, name=self.name)

    def get_args(self) -> Iterable[Self]:
        return self.args

    def __repr__(self) -> str:
        return self.full_name()

    def full_name(self) -> str:
        return f'{super(GenericTypeHint, self).full_name()}[{", ".join(arg.full_name() for arg in self.args)}]'

    @property
    def origin(self) -> TypeHint:
        return TypeHint(module=self.module, name=self.name)

    def __eq__(self, other) -> bool:
        return super(GenericTypeHint, self).__eq__(other) and (
            isinstance(other, GenericTypeHint) and self.args == other.args
        )

    def __hash__(self) -> int:
        hash_ = super(GenericTypeHint, self).__hash__()
        for arg in self.args:
            hash_ = (hash_ << 1) + arg.__hash__()
        return hash_


class NoneTypeHint(TypeHint):
    def __init__(self):
        super().__init__(module='types', name='NoneType')

    def full_name(self):
        return 'None'

    def imports(self) -> Iterable[str]:
        return ()

    def __eq__(self, other) -> bool:
        return isinstance(other, NoneTypeHint)

    def __hash__(self) -> int:
        return -1

    def is_none(self) -> bool:
        return True


NONE = NoneTypeHint()


def list_of(item: TypeHint) -> TypeHint:
    return GenericTypeHint(module='builtins', name='list', args=(item,))


def union_of(*types: TypeHint) -> TypeHint:
    if not types:
        return NONE
    if len(types) == 1:
        return next(iter(types))

    args: set[TypeHint] = set()
    for typ in types:
        if typ and typ.is_union():
            args.update(cast(GenericTypeHint, typ).args)
        else:
            args.add(typ)
    return GenericTypeHint(module='typing', name='Union', args=sorted(args, key=str))


def flatten(types: Iterable[TypeHint]) -> Iterable[TypeHint]:
    all_types = set()
    _flatten(types, all_types)
    return all_types


def _flatten(types: Iterable[TypeHint], target: MutableSet[TypeHint]) -> None:
    for typ in types:
        target.add(typ.get_origin())
        _flatten(typ.get_args(), target)


def tuple_of(*types: TypeHint) -> TypeHint:
    assert len(types) > 1
    return GenericTypeHint(
        module='builtins',
        name='tuple',
        args=tuple(types),
    )


def optional(typ: TypeHint) -> TypeHint:
    return union_of(typ, NONE)
