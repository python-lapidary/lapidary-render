from __future__ import annotations

import logging
from types import NoneType
from typing import Any

from openapi_pydantic.v3.v3_1 import schema as schema31

from . import openapi, python
from .metamodel import MetaModel
from .refs import resolve_ref, resolve_refs_recursive
from .stack import Stack

logger = logging.getLogger(__name__)


class OpenApi30SchemaConverter:
    def __init__(
        self,
        schema: openapi.Schema | bool | None,
        stack: Stack,
        root_package: python.ModulePath,
        source: openapi.OpenAPI,
    ) -> None:
        self.schema = schema
        self.stack = stack
        self.root_package = root_package

        self.model = MetaModel(
            stack=stack.push('schema', stack.top()),
        )

        # source is needed by @resolve_ref mechanism
        self.source = source

    def process_schema(
        self,
    ) -> MetaModel | None:
        """Return MetaModel for schema or None if schema could never validate any values."""

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

    def process_schema_title(self, value: str, _: Stack) -> None:
        self.model.title = value

    def process_schema_description(self, value: str, _: Stack) -> None:
        self.model.description = value

    def process_schema_type(self, value: openapi.DataType, _: Stack):
        typ = {schema31.DataType[value.name]}
        assert isinstance(self.schema, openapi.Schema)
        if self.schema.nullable:
            typ.add(schema31.DataType.NULL)
        self.model.type_ = self.model.type_.intersection(typ) if self.model.type_ else typ

    def process_schema_nullable(self, value: openapi.DataType, _: Stack) -> None:
        pass

    def process_schema_enum(self, value: list[Any], _: Stack) -> None:
        enum_types = set(PY_TYPE_TO_JSON_TYPE[type(enum_value)] for enum_value in value)

        allowed_types = enum_types.intersection(self.model.type_) if self.model.type_ else enum_types
        allowed_py_types = tuple(JSON_TYPE_TO_PY_TYPE[typ] for typ in allowed_types)
        new_enum_values = {enum_value for enum_value in value if isinstance(enum_value, allowed_py_types)}

        self.model.enum = new_enum_values
        self.model.type_ = allowed_types

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

    @resolve_ref
    def process_schema_items(self, value: openapi.Schema, stack: Stack) -> None:
        self.model.items = self._process_subschema(value, stack)

    def process_schema_properties(self, value: dict[str, openapi.Schema], stack: Stack) -> None:
        for name, sub_schema in value.items():
            sub_stack = stack.push(name)
            if isinstance(sub_schema, openapi.Reference):
                sub_schema, path = resolve_refs_recursive(self.source, sub_schema)
                sub_stack = Stack.from_str(path)

            if prop_model := self._process_subschema(sub_schema, sub_stack):
                self.model.properties[name] = prop_model

    @resolve_ref
    def _process_subschema(self, value: openapi.Schema, stack: Stack) -> MetaModel | None:
        return OpenApi30SchemaConverter(value, stack, self.root_package, self.source).process_schema()

    def process_schema_additionalProperties(self, value: openapi.Schema | bool, stack: Stack) -> None:
        self.model.additional_props = self._process_subschema(value, stack) or False

    def process_schema_required(self, value: list[str], _) -> None:
        self.model.props_required = set(value)

    def _process_subschemas(self, value: list[openapi.Schema], stack: Stack) -> list[MetaModel]:
        return list(
            filter(
                None,
                [self._process_subschema(item_schema, stack.push(str(idx))) for idx, item_schema in enumerate(value)],
            )
        )

    def process_schema_oneOf(self, value: list[openapi.Schema], stack: Stack) -> None:
        self.model.one_of = self._process_subschemas(value, stack)

    def process_schema_anyOf(self, value: list[openapi.Schema], stack: Stack) -> None:
        self.model.any_of = self._process_subschemas(value, stack)

    def process_schema_allOf(self, value: list[openapi.Schema], stack: Stack) -> None:
        self.model.all_of = self._process_subschemas(value, stack)

    def process_schema_xml(self, *_) -> None:
        pass

    def process_schema_example(self, *_) -> None:
        pass

    def process_schema_examples(self, *_) -> None:
        pass


JSON_TYPE_TO_PY_TYPE = {
    schema31.DataType.STRING: str,
    schema31.DataType.INTEGER: int,
    schema31.DataType.BOOLEAN: bool,
    schema31.DataType.NUMBER: float,
    schema31.DataType.ARRAY: list,
    schema31.DataType.OBJECT: dict,
    schema31.DataType.NULL: NoneType,
}

PY_TYPE_TO_JSON_TYPE = {value: key for key, value in JSON_TYPE_TO_PY_TYPE.items()}
