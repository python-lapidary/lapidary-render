from __future__ import annotations

import dataclasses as dc
from collections.abc import Iterable, Mapping, Sequence


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
class AnnotatedType:
    typ: NameRef
    generic_args: Sequence[AnnotatedType] = dc.field(default_factory=tuple)
    gt: int | float | None = None
    ge: int | float | None = None
    lt: int | float | None = None
    le: int | float | None = None
    multiple_of: int | float | None = None
    pattern: str | None = None
    min_length: int | None = None
    max_length: int | None = None

    def __post_init__(self):
        assert isinstance(self.typ, NameRef), self.typ

    def num_constraints(self) -> Iterable[tuple[NameRef, int | float]]:
        for key, typ in CONSTRAINTS.items():
            if (value := getattr(self, key)) is not None:
                yield typ, value

    def dependencies(self) -> Iterable[NameRef]:
        yield self.typ
        yield from (item[0] for item in self.num_constraints())
        if self.pattern:
            yield NameRef('pydantic', 'Field')
        for arg in self.generic_args:
            yield from arg.dependencies()

    @staticmethod
    def from_type(
        typ: type,
        generic: Sequence[AnnotatedType] = (),
    ) -> AnnotatedType:
        return AnnotatedType(NameRef.from_type(typ), generic)


CONSTRAINTS: Mapping[str, NameRef] = {
    'lt': NameRef('annotated_types', 'Lt'),
    'le': NameRef('annotated_types', 'Le'),
    'gt': NameRef('annotated_types', 'Gt'),
    'ge': NameRef('annotated_types', 'Ge'),
    'max_length': NameRef('annotated_types', 'MaxLen'),
    'min_length': NameRef('annotated_types', 'MinLen'),
    'multiple_of': NameRef('annotated_types', 'MultipleOf'),
}

# don't use from_type(types.NoneType): https://github.com/python/cpython/issues/128197
NoneMetaType = AnnotatedType(NameRef('types', 'NoneType'))
_UNION = NameRef('typing', 'Union')


def list_of(item: AnnotatedType) -> AnnotatedType:
    return AnnotatedType(NameRef('builtins', 'list'), (item,))


def union_of(*types: AnnotatedType) -> AnnotatedType:
    args: set[AnnotatedType] = set()
    for typ in types:
        if typ.typ == _UNION:
            args.update(typ.generic_args)
        else:
            args.add(typ)

    if not args:
        return NoneMetaType
    if len(args) == 1:
        return next(iter(args))

    return AnnotatedType(_UNION, tuple(sorted(args, key=str)))


def tuple_of(*types: AnnotatedType) -> AnnotatedType:
    return AnnotatedType(NameRef('builtins', 'tuple'), tuple(types))


def optional(typ: AnnotatedType) -> AnnotatedType:
    return union_of(typ, NoneMetaType)
