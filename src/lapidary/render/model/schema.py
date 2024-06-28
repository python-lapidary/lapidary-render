import itertools
import logging
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

        name = value.lapidary_name or names.maybe_mangle_name(stack.top())
        base_type = (
            python.TypeHint.from_type(Exception)
            if value.lapidary_model_type is openapi.LapidaryModelType.exception
            else python.TypeHint.from_str('lapidary.runtime:ModelBase')
        )

        stack_props = stack.push('properties')
        fields = [
            self.process_property(prop_schema, stack_props.push(prop_name), prop_name, prop_name in value.required)
            for prop_name, prop_schema in value.properties.items()
        ]

        model_type = (
            python.ModelType[value.lapidary_model_type.name] if value.lapidary_model_type else python.ModelType.model
        )

        type_hint = resolve_type_hint(str(self.root_package), stack.push('schema', name))
        schema_class = python.SchemaClass(
            class_name=name,
            base_type=base_type,
            allow_extra=value.additional_properties is not False,
            fields=fields,
            docstr=value.description or None,
            model_type=model_type,
        )
        self.schema_types[stack] = schema_class, type_hint
        return type_hint

    @resolve_ref
    def process_property(self, value: openapi.Schema, stack: Stack, prop_name: str, required: bool) -> python.Field:
        name = names.maybe_mangle_name(prop_name)

        field_props = {FIELD_PROPS[k]: getattr(value, k) for k in value.model_fields_set if k in FIELD_PROPS}
        for k, v in field_props.items():
            if isinstance(v, str):
                if k == 'pattern':
                    field_props[k] = f"r'{v}'"
                else:
                    field_props[k] = f"'{v}'"

        if name != prop_name:
            field_props['alias'] = f"'{prop_name}'"

        typ = self.process_schema(value, stack)
        if value.nullable or not required or value.read_only or value.write_only:
            typ = python.GenericTypeHint.union_of(typ, python.NONE)

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
        if value.any_of:
            return self._get_composite_type_hint(stack.push('anyOf'), value.any_of)
        elif value.one_of:
            return self._get_one_of_type_hint(stack.push('oneOf'), value.one_of)
        elif value.all_of:
            return self._get_composite_type_hint(stack.push('allOf'), value.all_of)
        elif value.not_:
            raise NotImplementedError(stack.push('not'))
        elif value.type in PRIMITIVE_TYPES:
            return python.BuiltinTypeHint.from_str(PRIMITIVE_TYPES[value.type].__name__)
        elif value.type == openapi.Type.object:
            return self._process_schema_object(value, stack)
        elif value.type == openapi.Type.array:
            return python.GenericTypeHint.list_of(self.process_schema(value.items, stack.push('items')))
        elif value.type is None:
            return python.TypeHint.from_str('typing:Any')
        else:
            raise NotImplementedError(str(stack))

    @property
    def schema_modules(self) -> Iterable[python.SchemaModule]:
        modules: dict[python.ModulePath, list[python.SchemaClass]] = defaultdict(list)
        for pointer, schema_class_type in self.schema_types.items():
            schema_class, hint = schema_class_type
            modules[python.ModulePath(hint.module, is_module=True)].append(schema_class)
        return [
            python.SchemaModule(
                path=module,
                body=classes,
            )
            for module, classes in modules.items()
        ]


PRIMITIVE_TYPES = {
    openapi.Type.string: str,
    openapi.Type.integer: int,
    openapi.Type.number: float,
    openapi.Type.boolean: bool,
}

FIELD_PROPS = {
    'exclusive_maximum': 'lt',
    'exclusive_minimum': 'gt',
    'maximum': 'le',
    'max_items': 'max_length',
    'max_length': 'max_length',
    'max_properties': 'min_length',
    'minimum': 'ge',
    'min_items': 'min_length',
    'min_length': 'min_length',
    'min_properties': 'min_length',
    'multiple_of': 'multiple_of',
    'pattern': 'pattern',
}


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
