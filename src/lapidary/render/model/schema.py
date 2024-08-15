import datetime as dt
import decimal as dec
import itertools
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable, MutableMapping, Sequence

import typing_extensions as typing

from .. import json_pointer, names
from . import openapi, python
from .refs import resolve_ref
from .stack import Stack

type ResolveRefFn[Target] = Callable[[openapi.Reference[Target]], tuple[Stack, Target]]

logger = logging.getLogger(__name__)


class OpenApi30SchemaConverter:
    def __init__(self, root_package: python.ModulePath, resolve_ref_: ResolveRefFn) -> None:
        self.root_package = root_package
        self.resolve_ref = staticmethod(resolve_ref_)
        self.schema_types: MutableMapping[Stack, tuple[python.SchemaClass, python.TypeHint]] = {}

    @resolve_ref
    def _process_schema_object(self, value: openapi.Schema, stack: Stack) -> python.TypeHint:
        if stack in self.schema_types:
            return self.schema_types[stack][1]

        name = value.lapidary_name or names.maybe_mangle_name(stack.top())
        stack_props = stack.push('properties')
        fields = [
            self.process_property(prop_schema, stack_props.push(prop_name), prop_name, prop_name in value.required)
            for prop_name, prop_schema in value.properties.items()
        ]

        type_hint = resolve_type_hint(str(self.root_package), stack.push('schema', name))
        schema_class = python.SchemaClass(
            class_name=name,
            base_type=python.TypeHint.from_str('lapidary.runtime:ModelBase'),
            allow_extra=value.additional_properties is not False,
            fields=fields,
            docstr=value.description or None,
        )
        self.schema_types[stack] = schema_class, type_hint
        return type_hint

    @resolve_ref
    def process_property(self, value: openapi.Schema, stack: Stack, prop_name: str, in_required: bool) -> python.Field:
        name = names.maybe_mangle_name(prop_name)

        typ = self.process_schema(value, stack)
        if not in_required:
            typ = python.union_of(typ, python.NONE)

        field_props = {}
        allowed_field_props = (
            NUMERIC_CONSTRAINTS
            if in_types(
                typ,
                (
                    python.TypeHint.from_type(int),
                    python.TypeHint.from_type(float),
                    python.TypeHint.from_type(dec.Decimal),
                    python.NONE,
                ),
            )
            else None
        )

        for k in value.model_fields_set:
            v = getattr(value, k)

            if k == 'maximum':
                field_prop = 'lt' if value.exclusive_maximum else 'le'
                field_props[field_prop] = v
                continue
            if k == 'minimum':
                field_prop = 'gt' if value.exclusive_minimum else 'ge'
                field_props[field_prop] = v
                continue
            if k not in FIELD_PROPS:
                continue

            field_prop = FIELD_PROPS[k]
            if allowed_field_props is not None and field_prop not in allowed_field_props:
                logger.warning('Ignoring unsupported constraint (%s) for type %s', field_prop, typ)
                continue

            if isinstance(v, str):
                if field_prop == 'pattern':
                    field_props[field_prop] = f"r'{v}'"
                else:
                    field_props[field_prop] = f"'{v}'"
            else:
                field_props[field_prop] = v

        if name != prop_name:
            field_props['alias'] = f"'{prop_name}'"

        required = in_required and not (value.read_only or value.write_only)

        return python.Field(
            name=name,
            annotation=python.Annotation(
                type=typ,
                field_props=field_props,
            ),
            required=required,
        )

    @resolve_ref
    def process_schema(self, value: openapi.Schema, stack: Stack, required: bool = True) -> python.TypeHint:
        assert isinstance(value, openapi.Schema)
        logger.debug('Process schema %s', stack)

        typ = self._process_schema(value, stack)

        if value.nullable or not required or value.read_only or value.write_only:
            typ = python.union_of(typ, python.NONE)

        return typ

    def _get_one_of_type_hint(
        self,
        stack: Stack,
        one_of: Iterable[openapi.Reference[openapi.Schema] | openapi.Schema],
    ) -> python.TypeHint:
        return python.union_of(
            *tuple(self.process_schema(sub_schema, stack.push(str(idx))) for idx, sub_schema in enumerate(one_of))
        )

    def _get_composite_type_hint(
        self,
        stack: Stack,
        schemas: list[openapi.Schema | openapi.Reference],
    ) -> python.TypeHint:
        if len(schemas) != 1:
            raise NotImplementedError(stack, 'Multiple component schemas (allOf, anyOf) are currently unsupported.')

        return self.process_schema(schemas[0], stack)

    def _process_schema(
        self,
        value: openapi.Schema,
        stack: Stack,
    ) -> python.TypeHint:
        if value.any_of:
            return self._get_composite_type_hint(stack.push('anyOf'), value.any_of)
        elif value.one_of:
            return self._get_one_of_type_hint(stack.push('oneOf'), value.one_of)
        elif value.all_of:
            return self._get_composite_type_hint(stack.push('allOf'), value.all_of)
        elif value.not_:
            raise NotImplementedError(stack.push('not'))
        elif value.type == openapi.Type.string and value.format:
            return self._process_string(value, stack)
        elif value.type in PRIMITIVE_TYPES:
            return python.TypeHint.from_type(PRIMITIVE_TYPES[value.type])
        elif value.type == openapi.Type.object:
            return self._process_schema_object(value, stack)
        elif value.type == openapi.Type.array:
            return python.list_of(self.process_schema(value.items, stack.push('items')))
        elif value.type is None:
            return python.TypeHint.from_str('typing:Any')
        else:
            raise NotImplementedError(str(stack))

    def _process_string(self, value: openapi.Schema, _: Stack) -> python.TypeHint:
        if value.format:
            if typ := FORMAT_ENCODERS.get((value.type, value.format), None):
                return python.TypeHint.from_type(typ)
        return python.TypeHint.from_type(str)

    @property
    def schema_modules(self) -> Iterable[python.SchemaModule]:
        modules: dict[python.ModulePath, list[python.SchemaClass]] = defaultdict(list)
        for schema_class_type in self.schema_types.values():
            schema_class, hint = schema_class_type
            modules[python.ModulePath(hint.module, is_module=True)].append(schema_class)
        return [
            python.SchemaModule(
                path=module,
                body=classes,
            )
            for module, classes in modules.items()
        ]


def in_types(typ: python.TypeHint, allowed: Iterable[python.TypeHint]) -> bool:
    if typ.is_union():
        return all(in_types(arg, allowed) for arg in typing.cast(python.GenericTypeHint, typ).args)

    return typ in allowed


PRIMITIVE_TYPES = {
    openapi.Type.string: str,
    openapi.Type.integer: int,
    openapi.Type.number: float,
    openapi.Type.boolean: bool,
}

FORMAT_ENCODERS = {
    (openapi.Type.string, 'uuid'): uuid.UUID,
    (openapi.Type.string, 'date'): dt.date,
    (openapi.Type.string, 'date-time'): dt.datetime,
    (openapi.Type.string, 'time'): dt.time,
    (openapi.Type.string, 'decimal'): dec.Decimal,
}

FIELD_PROPS = {
    'max_items': 'max_length',
    'max_length': 'max_length',
    'max_properties': 'man_length',
    'min_items': 'min_length',
    'min_length': 'min_length',
    'min_properties': 'min_length',
    'multiple_of': 'multiple_of',
    'pattern': 'pattern',
}

NUMERIC_CONSTRAINTS = {'ge', 'gt', 'le', 'lt', 'multiple_of'}


def resolve_type_hint(root_package: str, pointer: str | Stack) -> python.TypeHint:
    if isinstance(pointer, Stack):
        parts: Sequence[str] = pointer.path[1:]
    else:
        parts = pointer.split('/')[1:]
    module_name = '.'.join(
        itertools.chain(
            (root_package,), [names.maybe_mangle_name(json_pointer.decode_json_pointer(part)) for part in parts[:-1]]
        )
    )
    top = names.maybe_mangle_name(parts[-1])
    return python.TypeHint(module=module_name, name=top)
