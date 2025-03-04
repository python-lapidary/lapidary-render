from typing import Union

import pytest
from openapi_pydantic.v3.v3_1 import DataType

from lapidary.render.model.conv_schema import OpenApi30SchemaConverter
from lapidary.render.model.openapi import Schema
from lapidary.render.model.python import (
    AnnotatedType,
    AnnotatedVariable,
    ModulePath,
    NameRef,
    SchemaClass,
)
from lapidary.render.model.stack import Stack
from lapidary.render.runtime import JsonValue, ModelBase


def test_no_type_is_json_value():
    converter = OpenApi30SchemaConverter(Schema(), Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    annotation = converter.process_schema().as_annotation('root')
    assert annotation == JsonValue


@pytest.mark.skip('error')
def test_additional_properties_schema():
    schema = Schema(
        type=DataType.OBJECT,
        additionalProperties=Schema(
            type=DataType.STRING,
        ),
    )
    converter = OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    annotation = converter.process_schema().as_annotation('root')
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
    schema = Schema(
        type=DataType.OBJECT,
        properties={'prop1': Schema(type=DataType.NUMBER)},
        additionalProperties=Schema(
            type=DataType.STRING,
        ),
    )
    converter = OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    typ = converter.process_schema().as_type('root')
    assert '__pydantic_extra__' in [field.name for field in typ.fields]


@pytest.mark.skip('not implemented')
def test_named_nullable_ignored():
    """
    pydantic.JsonValue is nullable (Union with None) while in OpenAPI 3.0 flavor of JSON Schema, an empty schema is not
    """
    schema = Schema(nullable=True)
    converter = OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    typ = converter.process_schema().as_annotation('root')
    #
    assert typ != JsonValue


@pytest.mark.skip('buggy')
def test_doesnt_make_nullable_with_enum():
    """Parent schema is not nullable so resulting type shouldn't be either"""
    schema = Schema(
        anyOf=[
            Schema(type=DataType.STRING),
            Schema(enum=[None]),
        ]
    )
    converter = OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    typ = converter.process_schema().as_annotation('root')
    expected = AnnotatedType(NameRef.from_type(str))
    assert typ == expected


@pytest.mark.skip('not implemented')
def test_read_write_property():
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
    converter = OpenApi30SchemaConverter(schema, Stack(('#', 'schemas', 'model')), ModulePath('root'), None)
    model = converter.process_schema().as_type('root')
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
