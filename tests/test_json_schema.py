import types
from typing import Union

import pytest
from openapi_pydantic.v3.v3_1 import DataType

from lapidary_render.model import conv_schema
from lapidary_render.model.openapi import Schema
from lapidary_render.model.python import (
    AnnotatedType,
    AnnotatedVariable,
    ModulePath,
    NameRef,
    SchemaClass,
)
from lapidary_render.model.python.type_hint import union_of
from lapidary_render.model.stack import Stack
from lapidary_render.runtime import ModelBase


@pytest.mark.skip('error')
def test_additional_properties_schema():
    # docs/json-schema.md#additionalproperties — schema value generates typed dict annotation
    schema = Schema(
        type=DataType.OBJECT,
        additionalProperties=Schema(
            type=DataType.STRING,
        ),
    )
    converter = conv_schema.OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    annotation = conv_schema.as_annotation(converter.process_schema(), 'root')
    expected = AnnotatedType(
        NameRef.from_type(dict),
        (
            AnnotatedType(NameRef.from_type(str)),
            AnnotatedType(NameRef.from_type(str)),
        ),
    )
    assert annotation == expected


@pytest.mark.skip('not implemented')
def test_properties_and_additional_properties_schema():
    # docs/json-schema.md#additionalproperties — schema value alongside explicit properties generates __pydantic_extra__ field
    schema = Schema(
        type=DataType.OBJECT,
        properties={'prop1': Schema(type=DataType.NUMBER)},
        additionalProperties=Schema(
            type=DataType.STRING,
        ),
    )
    converter = conv_schema.OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    typ = conv_schema.as_type(converter.process_schema(), 'root')
    assert '__pydantic_extra__' in [field.name for field in typ.fields]


@pytest.mark.skip('buggy')
def test_doesnt_make_nullable_with_enum():
    # docs/json-schema.md#nullable-and-enum — null in enum requires type + nullable:true; without them null is excluded
    schema = Schema(
        anyOf=[
            Schema(type=DataType.STRING),
            Schema(enum=[None]),
        ]
    )
    converter = conv_schema.OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    typ = conv_schema.as_annotation(converter.process_schema(), 'root')
    expected = AnnotatedType(NameRef.from_type(str))
    assert typ == expected


@pytest.mark.skip('not implemented')
def test_read_write_property():
    # docs/json-schema.md#writeonly-readonly-and-non-required-properties — readOnly/writeOnly allOf merge produces optional union field
    schema = Schema(
        type=DataType.OBJECT,
        allOf=[
            Schema(
                properties={
                    'prop1': Schema(
                        type=DataType.NUMBER,
                        readOnly=True,
                    )
                }
            ),
            Schema(
                properties={
                    'prop1': Schema(
                        type=DataType.STRING,
                        writeOnly=True,
                    )
                }
            ),
        ],
    )
    converter = conv_schema.OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    model = conv_schema.as_type(converter.process_schema(), 'root')
    expected = SchemaClass(
        name='model',
        base_type=ModelBase,
        fields=[
            AnnotatedVariable(
                'prop1',
                AnnotatedType(
                    NameRef.from_type(Union),
                    (
                        AnnotatedType(NameRef.from_type(str)),
                        AnnotatedType(NameRef.from_type(int)),
                    ),
                ),
                required=True,
                alias=None,
            )
        ],
    )
    assert model == expected


def test_anyof_nullable_is_optional():
    # docs/json-schema.md#type-and-nullable — anyOf with nullable sub-schema produces Union including None
    schema = Schema(
        anyOf=[
            Schema(
                type=DataType.STRING,
            ),
            Schema(
                type=DataType.INTEGER,
                nullable=True,
            ),
        ],
    )
    converter = conv_schema.OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    annotation = conv_schema.as_annotation(
        converter.process_schema(),
        'root',
        True,
    )
    expected = union_of(*(AnnotatedType.from_type(t) for t in (str, int, types.NoneType)))
    assert annotation == expected
