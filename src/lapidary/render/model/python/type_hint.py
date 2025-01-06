from __future__ import annotations

import dataclasses as dc
from collections.abc import Iterable, Mapping, Sequence

from frozendict import frozendict


@dc.dataclass(slots=True, frozen=True)
class NameRef:
    """
    Name used as a reference, usually to a type or a function.
    Used to determine imports and in annotations.
    """

    module: str
    name: str

    def full_name(self) -> str:
        return self.module + ':' + self.name

    @staticmethod
    def from_str(path: str) -> NameRef:
        module, name = path.split(':')
        return NameRef(module=module, name=name)

    @staticmethod
    def from_type(typ: type) -> NameRef:
        if hasattr(typ, '__origin__'):
            raise ValueError('Generic types unsupported', typ)
        module = typ.__module__
        name = typ.__name__
        return NameRef(module=module, name=name)


@dc.dataclass(slots=True, frozen=True)
class GenericType:
    typ: NameRef
    generic_args: Sequence[AnnotatedType] = dc.field(default_factory=tuple)

    def __post_init__(self):
        assert isinstance(self.generic_args, tuple)
        for typ in self.generic_args:
            assert isinstance(typ, AnnotatedType)

    def dependencies(self) -> Iterable[NameRef]:
        yield self.typ
        for arg in self.generic_args:
            yield from arg.dependencies()


@dc.dataclass(slots=True, frozen=True)
class AnnotatedType:
    typ: GenericType
    constraints: Mapping[NameRef, int | float] = dc.field(default_factory=frozendict)
    pattern: str | None = None

    def __post_init__(self):
        assert isinstance(self.typ, GenericType), self.typ

    def dependencies(self) -> Iterable[NameRef]:
        yield from self.typ.dependencies()
        yield from (self.constraints or {}).keys()

    @staticmethod
    def from_type(typ: type) -> AnnotatedType:
        return AnnotatedType(GenericType(NameRef.from_type(typ)))


# don't use from_type(types.NoneType): https://github.com/python/cpython/issues/128197
NoneMetaType = AnnotatedType(GenericType(NameRef('types', 'NoneType')))
_UNION = NameRef('typing', 'Union')


def list_of(item: AnnotatedType) -> AnnotatedType:
    return AnnotatedType(GenericType(NameRef('builtins', 'list'), (item,)))


def union_of(*types: AnnotatedType) -> AnnotatedType:
    args: set[AnnotatedType] = set()
    for typ in types:
        if typ.typ.typ == _UNION:
            args.update(typ.typ.generic_args)
        else:
            args.add(typ)

    if not args:
        return NoneMetaType
    if len(args) == 1:
        return next(iter(args))

    return AnnotatedType(GenericType(_UNION, tuple(sorted(args, key=str))))


def tuple_of(*types: AnnotatedType) -> AnnotatedType:
    return AnnotatedType(GenericType(NameRef('builtins', 'tuple'), tuple(types)))


def optional(typ: AnnotatedType) -> AnnotatedType:
    return union_of(typ, NoneMetaType)
