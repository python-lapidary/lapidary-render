from __future__ import annotations

import datetime as dt
import importlib
import logging
from typing import Union
from uuid import UUID

from pydantic import BaseModel, Extra

from .refs import ResolverFunc
from .. import openapi
from ..absent import Absent
from ..module_path import ModulePath

logger = logging.getLogger(__name__)

STRING_FORMATS = {
    'uuid': UUID,
    'date': dt.date,
    'date-time': dt.datetime,
}

PRIMITIVE_TYPES = {
    openapi.Type.string: str,
    openapi.Type.integer: int,
    openapi.Type.number: float,
    openapi.Type.boolean: bool,
}


def get_type_hint(schema: openapi.Schema, module: ModulePath, name: str, required: bool,
                  resolver: ResolverFunc) -> TypeHint:
    typ = _get_type_hint(schema, module, name, resolver)

    if schema.nullable:
        typ = typ.union_with(BuiltinTypeHint.from_str('None'))
    if not required:
        typ = typ.union_with(TypeHint.from_type(Absent))

    return typ


def _get_one_of_type_hint(schema: openapi.Schema, module: ModulePath, name: str, resolve: ResolverFunc) -> TypeHint:
    args = []
    for idx, sub_schema in enumerate(schema.oneOf):
        if isinstance(sub_schema, openapi.Reference):
            sub_schema, sub_module, sub_name = resolve(sub_schema, openapi.Schema)
        else:
            sub_name = name + str(idx)
            sub_module = module

        if sub_schema.lapidary_name is not None:
            sub_name = sub_schema.lapidary_name

        type_hint = get_type_hint(sub_schema, sub_module, sub_name, True, resolve)
        args.append(type_hint)

    return GenericTypeHint(
        module='typing',
        name='Union',
        args=tuple(args),
    )


def _get_composite_type_hint(
        component_schemas: list[Union[openapi.Schema, openapi.Reference]], module: ModulePath, name: str, resolve: ResolverFunc
) -> TypeHint:
    if len(component_schemas) != 1:
        raise NotImplementedError(name, 'Multiple component schemas (allOf, anyOf, oneOf) are currently unsupported.')

    return resolve_type_hint(component_schemas[0], module, name, resolve)


def _get_type_hint(schema: openapi.Schema, module: ModulePath, name: str, resolver: ResolverFunc) -> TypeHint:
    class_name = name.replace(' ', '_')
    if schema.enum:
        return TypeHint(module=module.str(), name=class_name)
    elif schema.type == openapi.Type.string:
        return TypeHint.from_type(STRING_FORMATS.get(schema.format, str))
    elif schema.type in PRIMITIVE_TYPES:
        return BuiltinTypeHint.from_str(PRIMITIVE_TYPES[schema.type].__name__)
    elif schema.type == openapi.Type.object:
        return _get_type_hint_object(schema, module, class_name)
    elif schema.type == openapi.Type.array:
        return _get_type_hint_array(schema, module, class_name, resolver)
    elif schema.anyOf:
        return _get_composite_type_hint(schema.anyOf, module, class_name, resolver)
    elif schema.oneOf:
        return _get_one_of_type_hint(schema, module, class_name, resolver)
    elif schema.allOf:
        return _get_composite_type_hint(schema.allOf, module, class_name, resolver)
    elif schema.type is None:
        return TypeHint.from_str('typing.Any')
    else:
        raise NotImplementedError


def _get_type_hint_object(schema: openapi.Schema, module: ModulePath, name: str) -> TypeHint:
    if schema.properties or schema.allOf:
        return TypeHint(module=module.str(), name=name)
    else:
        return TypeHint(module=module.str(), name=name)


def _get_type_hint_array(schema: openapi.Schema, module: ModulePath, parent_name: str,
                         resolver: ResolverFunc) -> TypeHint:
    if isinstance(schema.items, openapi.Reference):
        item_schema, module, name = resolver(schema.items, openapi.Schema)
    else:
        item_schema = schema.items
        name = parent_name + 'Item'

    type_hint = get_type_hint(item_schema, module, name, True, resolver)
    return type_hint.list_of()


class TypeHint(BaseModel):
    module: str
    name: str

    class Config:
        extra = Extra.forbid

    def __repr__(self):
        return self.full_name()

    def full_name(self):
        return self.module + '.' + self.name if self.module != 'builtins' else self.name

    @staticmethod
    def from_str(path: str) -> TypeHint:
        module, name = path.rsplit('.', 1)
        return TypeHint(module=module, name=name)

    @staticmethod
    def from_type(typ: type) -> TypeHint:
        if hasattr(typ, '__origin__'):
            raise ValueError('Generic types unsupported', typ)
        module = typ.__module__
        name = typ.__name__
        if module == 'builtins':
            return BuiltinTypeHint.from_str(name)
        else:
            return TypeHint(module=module, name=name)

    def imports(self) -> list[str]:
        return [self.module]

    def union_with(self, other: TypeHint) -> GenericTypeHint:
        return GenericTypeHint(module='typing', name='Union', args=[self, other])

    def list_of(self) -> GenericTypeHint:
        return GenericTypeHint(module='builtins', name='list', args=[self])

    def _types(self) -> list[TypeHint]:
        return [self]

    def __eq__(self, other) -> bool:
        return (
                isinstance(other, TypeHint)
                # generic type hint has args, so either both should be generic or none
                and isinstance(self, GenericTypeHint) == isinstance(other, GenericTypeHint)
                and self.module == other.module
                and self.name == other.name
        )

    def __hash__(self) -> int:
        return self.module.__hash__() * 14159 + self.name.__hash__()

    def resolve(self) -> type:
        mod = importlib.import_module(self.module)
        return getattr(mod, self.name)


class BuiltinTypeHint(TypeHint):
    module: str = 'builtins'

    class Config:
        extra = Extra.forbid

    def __repr__(self):
        return self.full_name()

    @staticmethod
    def from_str(name: str) -> BuiltinTypeHint:
        return BuiltinTypeHint(name=name)

    def imports(self) -> list[str]:
        return []

    def full_name(self):
        return self.name


class GenericTypeHint(TypeHint):
    args: tuple[TypeHint, ...]

    class Config:
        extra = Extra.forbid

    def union_with(self, other: TypeHint) -> GenericTypeHint:
        if self.module == 'typing' and self.name == 'Union':
            return GenericTypeHint(module=self.module, name=self.name, args=[*self.args, other])
        else:
            return super().union_with(other)

    @staticmethod
    def union_of(types: tuple[TypeHint, ...]) -> GenericTypeHint:
        args = set()
        for typ in types:
            if isinstance(typ, GenericTypeHint) and typ.module == 'typing' and typ.name == 'Union':
                args.update(typ.args)
            else:
                args.add(typ)
        return GenericTypeHint(module='typing', name='Union', args=args)

    def imports(self) -> list[str]:
        return [
            imp
            for typ in self._types()
            for imp in TypeHint.imports(typ)
            if imp != 'builtins'
        ]

    def _types(self) -> list[TypeHint]:
        return [self, *[typ for arg in self.args for typ in arg._types()]]

    def resolve(self) -> type:
        generic = super().resolve()
        return generic[tuple(arg.resolve() for arg in self.args)]

    def __repr__(self) -> str:
        return self.full_name()

    def full_name(self) -> str:
        return f'{super().full_name()}[{", ".join(arg.full_name() for arg in self.args)}]'

    @property
    def origin(self) -> TypeHint:
        return TypeHint(module=self.module, name=self.name)

    def __eq__(self, other) -> bool:
        return (
                isinstance(other, GenericTypeHint)
                and self.module == other.module
                and self.name == other.name
                and self.args == other.args
        )

    def __hash__(self) -> int:
        hash_ = super().__hash__()
        for arg in self.args:
            hash_ = (hash_ << 1) + arg.__hash__()
        return hash_


def resolve_type_hint(typ: Union[openapi.Schema, openapi.Reference], module: ModulePath, name: str,
                      resolver: ResolverFunc) -> TypeHint:
    if isinstance(typ, openapi.Reference):
        typ, module, name = resolver(typ, openapi.Schema)
    return get_type_hint(typ, module, name, True, resolver)
