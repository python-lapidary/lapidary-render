from __future__ import annotations

import datetime as dt
import logging
import uuid

from lapidary.runtime.absent import Absent

from . import openapi, python
from .refs import ResolverFunc

logger = logging.getLogger(__name__)

STRING_FORMATS = {
    'uuid': uuid.UUID,
    'date': dt.date,
    'date-time': dt.datetime,
}

PRIMITIVE_TYPES = {
    openapi.Type.string: str,
    openapi.Type.integer: int,
    openapi.Type.number: float,
    openapi.Type.boolean: bool,
}


def get_type_hint(schema: openapi.Schema, module: python.ModulePath, name: str, required: bool,
                  resolver: ResolverFunc) -> python.TypeHint:
    typ = _get_type_hint(schema, module, name, resolver)

    if schema.nullable:
        typ = typ.union_with(python.BuiltinTypeHint.from_str('None'))
    if not required:
        typ = typ.union_with(python.TypeHint.from_type(Absent))

    return typ


def _get_one_of_type_hint(schema: openapi.Schema, module: python.ModulePath, name: str, resolve: ResolverFunc) -> python.TypeHint:
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

    return python.GenericTypeHint(
        module='typing',
        name='Union',
        args=tuple(args),
    )


def _get_composite_type_hint(
        component_schemas: list[openapi.Schema | openapi.Reference], module: python.ModulePath, name: str, resolve: ResolverFunc
) -> python.TypeHint:
    if len(component_schemas) != 1:
        raise NotImplementedError(name, 'Multiple component schemas (allOf, anyOf, oneOf) are currently unsupported.')

    return resolve_type_hint(component_schemas[0], module, name, resolve)


def _get_type_hint(schema: openapi.Schema, module: python.ModulePath, name: str, resolver: ResolverFunc) -> python.TypeHint:
    class_name = name.replace(' ', '_')
    if schema.enum:
        return python.TypeHint(module=str(module), name=class_name)
    elif schema.type == openapi.Type.string:
        return python.TypeHint.from_type(STRING_FORMATS.get(schema.format, str))
    elif schema.type in PRIMITIVE_TYPES:
        return python.BuiltinTypeHint.from_str(PRIMITIVE_TYPES[schema.type].__name__)
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
        return python.TypeHint.from_str('typing:Any')
    else:
        raise NotImplementedError


def _get_type_hint_object(schema: openapi.Schema, module: python.ModulePath, name: str) -> python.TypeHint:
    if schema.properties or schema.allOf:
        return python.TypeHint(module=str(module), name=name)
    else:
        return python.TypeHint(module=str(module), name=name)


def _get_type_hint_array(schema: openapi.Schema, module: python.ModulePath, parent_name: str,
                         resolver: ResolverFunc) -> python.TypeHint:
    if isinstance(schema.items, openapi.Reference):
        item_schema, module, name = resolver(schema.items, openapi.Schema)
    else:
        item_schema = schema.items
        name = parent_name + 'Item'

    type_hint = get_type_hint(item_schema, module, name, True, resolver)
    return type_hint.list_of()


def resolve_type_hint(typ: openapi.Schema | openapi.Reference, module: python.ModulePath, name: str,
                      resolver: ResolverFunc) -> python.TypeHint:
    if isinstance(typ, openapi.Reference):
        typ, module, name = resolver(typ, openapi.Schema)
    return get_type_hint(typ, module, name, True, resolver)
