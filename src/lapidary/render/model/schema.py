import datetime as dt
import itertools
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable, MutableMapping, Sequence

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

        name = value.lapidary_name or stack.top()
        base_type = (
            python.TypeHint.from_type(Exception)
            if value.lapidary_model_type is openapi.LapidaryModelType.exception
            else python.TypeHint.from_str('lapidary.runtime:ModelBase')
        )

        stack_attr = stack.push('properties')
        attributes = [
            self.process_property(prop_schema, stack_attr.push(prop_name), prop_name in value.required)
            for prop_name, prop_schema in value.properties.items()
        ]

        model_type = (
            python.ModelType[value.lapidary_model_type.name] if value.lapidary_model_type else python.ModelType.model
        )

        type_hint = resolve_type_hint(str(self.root_package), stack.push('schema', name))
        schema_class = python.SchemaClass(
            class_name=name,
            base_type=base_type,
            allow_extra=value.additionalProperties is not False,
            has_aliases=any(['alias' in attr.annotation.field_props for attr in attributes]),
            attributes=attributes,
            docstr=value.description or None,
            model_type=model_type,
        )
        self.schema_types[stack] = schema_class, type_hint
        return type_hint

    @resolve_ref
    def process_property(self, value: openapi.Schema, stack: Stack, required: bool) -> python.Attribute:
        alias = value.lapidary_name or names.maybe_mangle_name(stack.top())
        names.check_name(alias, False)

        return python.Attribute(
            name=alias,
            annotation=self.get_attr_annotation(value, stack, required),
            required=required,
        )

    @resolve_ref
    def get_attr_annotation(
        self,
        value: openapi.Schema,
        stack: Stack,
        required: bool,
    ) -> python.AttributeAnnotation:
        """
        if type is a schema, then it's a nested schema. Name should be parent_class_name+prop_name, and module is the same.
        Otherwise, it's a reference; schema, module and name should be resolved from it and used to generate type_ref
        """

        name = stack.top()

        field_props = {FIELD_PROPS[k]: getattr(value, k) for k in value.model_fields_set if k in FIELD_PROPS}
        for k, v in field_props.items():
            if isinstance(v, str):
                field_props[k] = f"'{v}'"

        # if schema.in_ is not None:
        #     field_props['in_'] = 'lapidary.runtime.ParamPlacement.' + schema.in_
        #     field_props['alias'] = f"'{schema.lapidary_name or name}'"

        if name is not None:
            field_props['alias'] = "'" + name + "'"

        if 'pattern' in value.model_fields_set:
            field_props['regex'] = f"r'{value.pattern}'"

        direction = get_direction(value.readOnly, value.writeOnly)
        if direction:
            field_props['direction'] = direction
            # TODO better handle direction

        typ = self.process_schema(value, stack)
        if value.nullable or not required or bool(direction):
            typ = python.GenericTypeHint.union_of(typ, python.NONE)

        return python.AttributeAnnotation(type=typ, field_props=field_props)

    @resolve_ref
    def process_schema(self, value: openapi.Schema, stack: Stack, required: bool = True) -> python.TypeHint:
        assert isinstance(value, openapi.Schema)
        logger.debug('Process schema %s', stack)

        typ = self._process_schema(value, stack)

        if value.nullable or not required:
            typ = python.GenericTypeHint.union_of(typ, python.NONE)

        return typ

    def _get_one_of_type_hint(
        self,
        stack: Stack,
        one_of: Iterable[openapi.Reference[openapi.Schema] | openapi.Schema],
    ) -> python.TypeHint:
        return python.GenericTypeHint.union_of(
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
        if value.type == openapi.Type.string:
            typ = STRING_FORMATS.get(value.format, str) if value.format else str
            return python.TypeHint.from_type(typ)
        elif value.type in PRIMITIVE_TYPES:
            return python.BuiltinTypeHint.from_str(PRIMITIVE_TYPES[value.type].__name__)
        elif value.type == openapi.Type.object:
            return self._process_schema_object(value, stack)
        elif value.type == openapi.Type.array:
            return python.GenericTypeHint.list_of(self.process_schema(value.items, stack.push('items')))
        elif value.anyOf:
            return self._get_composite_type_hint(stack.push('anyOf'), value.anyOf)
        elif value.oneOf:
            return self._get_one_of_type_hint(stack.push('oneOf'), value.oneOf)
        elif value.allOf:
            return self._get_composite_type_hint(stack.push('allOf'), value.allOf)
        elif value.type is None:
            return python.TypeHint.from_str('typing:Any')
        else:
            raise NotImplementedError

    @property
    def schema_modules(self) -> Iterable[python.SchemaModule]:
        modules: dict[python.ModulePath, list[python.SchemaClass]] = defaultdict(list)
        for pointer, schema_class_type in self.schema_types.items():
            schema_class, hint = schema_class_type
            modules[python.ModulePath(hint.module) / '__init__'].append(schema_class)
        return [
            python.SchemaModule(
                path=module,
                body=classes,
            )
            for module, classes in modules.items()
        ]


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

FIELD_PROPS = {
    'multipleOf': 'multiple_of',
    'maximum': 'le',
    'exclusiveMaximum': 'lt',
    'minimum': 'ge',
    'exclusiveMinimum': 'gt',
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'maxItems': 'max_items',
    'minItems': 'min_items',
    'uniqueItems': 'unique_items',
    'maxProperties': 'max_properties',
    'minProperties': 'min_properties',
}


def get_direction(read_only: bool | None, write_only: bool | None) -> str | None:
    if read_only:
        if write_only:
            raise ValueError()
        else:
            return 'lapidary.runtime.ParamDirection.read'
    else:
        if write_only:
            return 'lapidary.runtime.ParamDirection.write'
        else:
            return None


def resolve_type_hint(root_package: str, pointer: str | Stack) -> python.TypeHint:
    if isinstance(pointer, Stack):
        parts: Sequence[str] = pointer.path[1:]
    else:
        parts = pointer.split('/')[1:]
    module_name = '.'.join(
        itertools.chain(
            (root_package,), [names.maybe_mangle_name(json_pointer.encode_json_pointer(part)) for part in parts[:-1]]
        )
    )
    top: str | int = parts[-1]
    if isinstance(top, int):
        top = parts[-2] + str(top)
    assert isinstance(top, str)
    return python.TypeHint(module=module_name, name=top)
