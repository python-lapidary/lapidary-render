from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterable
from types import NoneType
from typing import Any

from openapi_pydantic.v3.v3_1 import schema as schema31

from . import openapi, python
from .metamodel import MetaModel, resolve_type_name
from .refs import resolve_ref, resolve_refs_recursive
from .stack import Stack

logger = logging.getLogger(__name__)


class OpenApi30SchemaConverter:
    def __init__(self, root_package: python.ModulePath, source: openapi.OpenAPI) -> None:
        self.root_package = root_package
        self.source = source
        self.type_models: set[Stack] = set()
        self.all_models: dict[Stack, MetaModel] = {}

    @resolve_ref
    def process_schema(
        self,
        value: openapi.Schema | bool | None,
        stack: Stack,
    ) -> MetaModel | None:
        if existing := self.all_models.get(stack):
            return existing

        if value is False or (isinstance(value, openapi.Schema) and value.enum and len(value.enum) == 0):
            return None

        model = MetaModel(
            stack=stack.push('schema', stack.top()),
        )

        if value in (True, None):
            self.all_models[stack] = model
            return model

        assert isinstance(value, openapi.Schema)
        for field_name in value.model_fields_set:
            field_stack = stack.push(field_name)
            try:
                process = getattr(self, f'process_schema_{field_name}')
                logger.debug('Processing property %s', field_stack)
                process(getattr(value, field_name), field_stack, model, value)
            except AttributeError:
                logger.debug('Unsupported property %s', field_stack)

        if model_ := model.normalize_model():
            self.all_models[stack] = model_
            return model_
        return None

    def process_schema_title(self, value: str, _: Stack, model: MetaModel, _1: openapi.Schema) -> None:
        model.title = value

    def process_schema_description(self, value: str, _: Stack, model: MetaModel, _1: openapi.Schema) -> None:
        model.description = value

    def process_schema_type(self, value: openapi.DataType, _: Stack, model: MetaModel, schema: openapi.Schema):
        typ = {schema31.DataType[value.name]}
        if schema.nullable:
            typ.add(schema31.DataType.NULL)
        model.type_ = model.type_.intersection(typ) if model.type_ else typ

    def process_schema_nullable(self, value: openapi.DataType, _: Stack, model: MetaModel, _1: openapi.Schema) -> None:
        pass

    def process_schema_enum(self, value: list[Any], _: Stack, model: MetaModel, _1: openapi.Schema) -> None:
        enum_types = set(PY_TYPE_TO_JSON_TYPE[type(enum_value)] for enum_value in value)

        allowed_types = enum_types.intersection(model.type_) if model.type_ else enum_types
        allowed_py_types = tuple(JSON_TYPE_TO_PY_TYPE[typ] for typ in allowed_types)
        new_enum_values = {enum_value for enum_value in value if isinstance(enum_value, allowed_py_types)}

        model.enum = new_enum_values
        model.type_ = allowed_types

    def process_schema_readOnly(self, value: bool, _, model: MetaModel, _1) -> None:
        model.read_only = value

    def process_schema_writeOnly(self, value: bool, _, model: MetaModel, _1) -> None:
        model.write_only = value

    def process_schema_maximum(self, value: float, _, model: MetaModel, schema: openapi.Schema) -> None:
        if schema.exclusiveMaximum:
            model.gt = value
        else:
            model.ge = value

    def process_schema_exclusiveMaximum(self, *_):
        pass

    def process_schema_minimum(self, value: float, _, model: MetaModel, schema: openapi.Schema) -> None:
        if schema.exclusiveMinimum:
            model.lt = value
        else:
            model.le = value

    def process_schema_exclusiveMinimum(self, *_):
        pass

    def process_schema_multipleOf(self, value: float, _, model: MetaModel, _1) -> None:
        model.multiple_of = value

    def process_schema_schema_format(self, value: str, _, model: MetaModel, _1) -> None:
        model.format = value

    def process_schema_pattern(self, value: str, _, model: MetaModel, _1) -> None:
        model.pattern = value

    def process_schema_maxLength(self, value: int, _, model: MetaModel, _1) -> None:
        model.max_length = value

    def process_schema_minLength(self, value: int, _, model: MetaModel, _1) -> None:
        model.min_length = value

    @resolve_ref
    def process_schema_items(self, value: openapi.Schema, stack: Stack, model: MetaModel, _1) -> None:
        model.items = self.process_type_schema(value, stack)

    def process_schema_properties(self, value: dict[str, openapi.Schema], stack: Stack, model: MetaModel, _) -> None:
        for name, sub_schema in value.items():
            sub_stack = stack.push(name)
            if isinstance(sub_schema, openapi.Reference):
                sub_schema, path = resolve_refs_recursive(self.source, sub_schema)
                sub_stack = Stack.from_str(path)

            if prop_model := self.process_type_schema(sub_schema, sub_stack):
                model.properties[name] = prop_model

    def process_schema_additionalProperties(
        self, value: openapi.Schema | bool, stack: Stack, model: MetaModel, _
    ) -> None:
        model.additional_props = self.process_type_schema(value, stack) or False

    def process_schema_required(self, value: list[str], _, model: MetaModel, _1) -> None:
        model.props_required = set(value)

    def _process_subschemas(self, value: list[openapi.Schema], stack: Stack) -> list[MetaModel]:
        return list(
            filter(
                None, [self.process_schema(item_schema, stack.push(str(idx))) for idx, item_schema in enumerate(value)]
            )
        )

    def process_schema_oneOf(self, value: list[openapi.Schema], stack: Stack, model: MetaModel, _) -> None:
        model.one_of = self._process_subschemas(value, stack)

    def process_schema_anyOf(self, value: list[openapi.Schema], stack: Stack, model: MetaModel, _) -> None:
        model.any_of = self._process_subschemas(value, stack)

    def process_schema_allOf(self, value: list[openapi.Schema], stack: Stack, model: MetaModel, _) -> None:
        model.all_of = self._process_subschemas(value, stack)

    def process_schema_xml(self, *_) -> None:
        pass

    def process_schema_example(self, *_) -> None:
        pass

    def process_schema_examples(self, *_) -> None:
        pass

    @resolve_ref
    def process_type_schema(self, value: openapi.Schema | bool | None, stack: Stack) -> MetaModel | None:
        """
        Type schemas are all schemas that should generate types: schemas used directly in OpenAPI, object properties and array items.
        Non-type schemas are schemas referenced in allOf, oneOf, anyOf and not.

        Generated types may be either classes or type aliases.

        :param value: OpenAPI Schema to process
        :param stack: path within the OpenAPI, used to generate FQN
        """
        logger.debug('Processing schema %s', stack)
        model = self.process_schema(value, stack)
        if model is None:
            return None

        # if not required:
        #     model |= NullModel()
        self.type_models.add(stack)

        return model

    @property
    def schema_modules(self) -> Iterable[python.SchemaModule]:
        modules: dict[python.ModulePath, list[python.SchemaClass]] = defaultdict(list)
        for stack, model in self.all_models.items():
            if stack not in self.type_models or model is None:
                continue
            types = list(model.as_types(str(self.root_package)))

            if types:
                modules[python.ModulePath(resolve_type_name(str(self.root_package), model.stack).typ.module)].extend(
                    types
                )
        return [
            python.SchemaModule(
                path=module,
                body=classes,
            )
            for module, classes in modules.items()
            if len(classes)
        ]


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

PRIMITIVE_TYPES = {
    openapi.DataType.STRING: str,
    openapi.DataType.INTEGER: int,
    openapi.DataType.NUMBER: float,
    openapi.DataType.BOOLEAN: bool,
}
