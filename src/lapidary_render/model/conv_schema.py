from __future__ import annotations

import logging
from typing import Any

from openapi_pydantic.v3.v3_1 import schema as schema31

from .. import json_pointer, names, runtime
from . import openapi, python, refs, schemamodel, stack

logger = logging.getLogger(__name__)


class OpenApi30SchemaConverter:
    """Preprocess openapi schema to SchemaModel"""

    def __init__(
        self,
        schema: openapi.Schema | bool | None,
        s: stack.Stack,
        root_package: python.ModulePath,
        source: openapi.OpenAPI,
    ) -> None:
        self.schema = schema
        self.stack = s
        self.root_package = root_package

        self.model = schemamodel.SchemaModel(
            stack=s.push('schema', s.top()),
        )

        # source is needed by @resolve_ref mechanism
        self.source = source

    def process_schema(
        self,
    ) -> schemamodel.SchemaModel | None:
        """Return SchemaModel for schema or None if schema could never validate any values."""

        logger.debug('Processing schema %s', self.stack)

        if self.schema is False or (
            isinstance(self.schema, openapi.Schema) and self.schema.enum and len(self.schema.enum) == 0
        ):
            return None

        assert isinstance(self.schema, openapi.Schema)
        for field_name in self.schema.model_fields_set:
            field_stack = self.stack.push(field_name)
            try:
                process = getattr(self, f'process_schema_{field_name}')
                logger.debug('Processing property %s', field_stack)
                process(getattr(self.schema, field_name), field_stack)
            except AttributeError:
                logger.debug('Unsupported property %s', field_stack)

        if model_ := self.model.normalize_model():
            return model_
        return None

    def process_schema_title(self, value: str, _: stack.Stack) -> None:
        self.model.title = value

    def process_schema_description(self, value: str, _: stack.Stack) -> None:
        self.model.description = value

    def process_schema_type(self, value: openapi.DataType, _: stack.Stack):
        self.model.type_ = {*(self.model.type_ or ()), schema31.DataType[value.name]}

    def process_schema_nullable(self, value: bool, _: stack.Stack) -> None:
        assert isinstance(self.schema, openapi.Schema)

        if self.schema.type and value:
            self.model.type_ = {*(self.model.type_ or ()), schema31.DataType.NULL}

    def process_schema_enum(self, value: list[Any], _: stack.Stack) -> None:
        self.model.enum = set(value)

    def process_schema_readOnly(self, value: bool, _) -> None:
        self.model.read_only = value

    def process_schema_writeOnly(self, value: bool, _) -> None:
        self.model.write_only = value

    def process_schema_maximum(self, value: float, _) -> None:
        assert isinstance(self.schema, openapi.Schema)
        if self.schema.exclusiveMaximum:
            self.model.lt = value
        else:
            self.model.le = value

    def process_schema_exclusiveMaximum(self, *_):
        pass

    def process_schema_minimum(self, value: float, _) -> None:
        assert isinstance(self.schema, openapi.Schema)
        if self.schema.exclusiveMinimum:
            self.model.gt = value
        else:
            self.model.ge = value

    def process_schema_exclusiveMinimum(self, *_):
        pass

    def process_schema_multipleOf(self, value: float, _) -> None:
        self.model.multiple_of = value

    def process_schema_schema_format(self, value: str, _) -> None:
        self.model.format = value

    def process_schema_pattern(self, value: str, _) -> None:
        self.model.pattern = value

    def process_schema_maxLength(self, value: int, _) -> None:
        self.model.max_length = value

    def process_schema_minLength(self, value: int, _) -> None:
        self.model.min_length = value

    @refs.resolve_ref
    def process_schema_items(self, value: openapi.Schema, s: stack.Stack) -> None:
        self.model.items = self._process_subschema(value, s)

    def process_schema_properties(self, value: dict[str, openapi.Schema], s: stack.Stack) -> None:
        for name, sub_schema in value.items():
            sub_stack = s.push(name)
            if isinstance(sub_schema, openapi.Reference):
                sub_schema, path = refs.resolve_refs_recursive(self.source, sub_schema)
                sub_stack = stack.Stack.from_str(path)

            if prop_model := self._process_subschema(sub_schema, sub_stack):
                self.model.properties[name] = prop_model

    @refs.resolve_ref
    def _process_subschema(self, value: openapi.Schema | bool, s: stack.Stack) -> schemamodel.SchemaModel | None:
        return OpenApi30SchemaConverter(value, s, self.root_package, self.source).process_schema()

    def process_schema_additionalProperties(self, value: openapi.Schema | bool, s: stack.Stack) -> None:
        self.model.additional_props = self._process_subschema(value, s) or False

    def process_schema_required(self, value: list[str], _) -> None:
        self.model.props_required = set(value)

    def _process_subschemas(self, value: list[openapi.Schema], s: stack.Stack) -> list[schemamodel.SchemaModel]:
        return list(
            filter(
                None,
                [self._process_subschema(item_schema, s.push(str(idx))) for idx, item_schema in enumerate(value)],
            )
        )

    def process_schema_oneOf(self, value: list[openapi.Schema], s: stack.Stack) -> None:
        self.model.one_of = self._process_subschemas(value, s)

    def process_schema_anyOf(self, value: list[openapi.Schema], s: stack.Stack) -> None:
        self.model.any_of = self._process_subschemas(value, s)

    def process_schema_allOf(self, value: list[openapi.Schema], s: stack.Stack) -> None:
        self.model.all_of = self._process_subschemas(value, s)

    def process_schema_xml(self, *_) -> None:
        pass

    def process_schema_example(self, *_) -> None:
        pass

    def process_schema_examples(self, *_) -> None:
        pass


FORMAT_ENCODERS = {
    (schema31.DataType.STRING, 'uuid'): python.NameRef.from_str('uuid:UUID'),
    (schema31.DataType.STRING, 'date'): python.NameRef.from_str('datetime:date'),
    (schema31.DataType.STRING, 'date-time'): python.NameRef.from_str('datetime:datetime'),
    (schema31.DataType.STRING, 'time'): python.NameRef.from_str('datetime:time'),
    (schema31.DataType.STRING, 'decimal'): python.NameRef.from_str('decimal:Decimal'),
}


def resolve_type_name(root_package: str, pointer: stack.Stack) -> python.AnnotatedType:
    # FIXME all fields should be saved as json ref; all schemas saved in a map with json ref as a key

    parts = [names.maybe_mangle_name(json_pointer.decode_json_pointer(part)) for part in pointer.path[1:]]
    module_name = '.'.join([root_package, *(part for part in parts[:-1])])
    top = parts[-1]
    return python.AnnotatedType(python.NameRef(module_name, top))


def as_type(model: schemamodel.SchemaModel, root_package: str) -> python.SchemaClass | None:
    """convert schema model, excluding any sub-schemas"""
    if model.any_of or not model.type_ or schema31.DataType.OBJECT not in model.type_ or model.is_any_obj():
        return None

    name = model.stack.top()  # TODO name = value.lapidary_name or s.top()
    fields = [
        _as_class_field(
            as_annotation(prop_model, root_package, prop_name in model.props_required),
            prop_name,
            prop_name in model.props_required,
        )
        for prop_name, prop_model in model.properties.items()
    ]
    return python.SchemaClass(
        name=names.maybe_mangle_name(name),
        base_type=runtime.ModelBase,
        allow_extra=model.additional_props is not False,
        fields=fields,
        docstr=model.description or None,
    )


def as_annotation(
    model: schemamodel.SchemaModel, root_package: str, required: bool = True, include_object: bool = True
) -> python.AnnotatedType:
    """
    Create type hint for the type represented by the source schema.

    In case where object schema with oneOf or anyOf is used, a type hint for the parent schema is created, and the
    items are rendered in as_type() as a synthetic class field.

    :param model: the schema model to convert
    :param root_package: root python package for object models
    :param required: if false, make the type a Union with None
    :param include_object: if true and the model type includes schema, include the class FQN in the resulting type hint
    """

    if not model.has_annotations():
        return runtime.JsonValue

    if model.any_of:
        return python.union_of(*[as_annotation(t, root_package, required) for t in model.any_of])

    else:
        types: set[python.AnnotatedType] = set()
        for schema_type in model.type_ or ():
            if include_object is False and schema_type == schema31.DataType.OBJECT:
                continue

            match schema_type:
                case schema31.DataType.STRING:
                    try:
                        typ = python.AnnotatedType(FORMAT_ENCODERS[(schema_type, model.format)])  # type: ignore[index]
                    except KeyError:
                        typ = _as_str_anno(model)
                case schema31.DataType.BOOLEAN:
                    typ = python.AnnotatedType.from_type(bool)
                case schema31.DataType.NUMBER:
                    typ = _as_numeric_anno(model, float)
                case schema31.DataType.INTEGER:
                    typ = _as_numeric_anno(model, int)
                case schema31.DataType.NULL:
                    typ = python.NoneMetaType
                case schema31.DataType.OBJECT:
                    typ = _as_object_anno(model, root_package)
                case schema31.DataType.ARRAY:
                    typ = python.list_of(
                        as_annotation(model.items, root_package) if model.items else runtime.JsonValue,
                    )
                case _:
                    raise TypeError(schema_type)
            types.add(typ)

    if not required:
        types.add(python.NoneMetaType)

    return python.union_of(*types)


def _as_class_field(anno: python.AnnotatedType, name: str, required: bool) -> python.AnnotatedVariable:
    python_name = names.maybe_mangle_name(name)
    return python.AnnotatedVariable(
        name=python_name,
        typ=anno,
        alias=name if name != python_name else None,
        required=required,
    )


def _as_numeric_anno(model: schemamodel.SchemaModel, typ: type) -> python.AnnotatedType:
    num_constraints = {'lt', 'gt', 'ge', 'le', 'multiple_of'}
    constraints = {}
    for key in num_constraints:
        if (value := getattr(model, key)) is not None:
            constraints[key] = typ(value)
    return python.AnnotatedType(
        python.NameRef.from_type(typ),
        **constraints,  # type: ignore[arg-type]
    )


def _as_str_anno(model: schemamodel.SchemaModel) -> python.AnnotatedType:
    str_constraints = {'max_length', 'min_length', 'pattern'}
    constraints = {key: value for key in str_constraints if (value := getattr(model, key)) is not None}
    return python.AnnotatedType(
        python.NameRef('builtins', 'str'),
        **constraints,  # type: ignore[arg-type]
    )


def _as_object_anno(model: schemamodel.SchemaModel, root_package: str) -> python.AnnotatedType:
    if not model.properties and not (
        any(sub.properties for sub in model.any_of or () if schema31.DataType.OBJECT in (sub.type_ or ()))
        and any(sub.properties for sub in model.one_of or () if schema31.DataType.OBJECT in (sub.type_ or ()))
    ):
        return runtime.JsonObject
    else:
        return resolve_type_name(root_package, model.stack)
