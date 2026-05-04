from openapi_pydantic.v3.v3_1 import DataType

from lapidary_render.model.schemamodel import SchemaModel
from lapidary_render.model.stack import Stack


def test_normalize_allof_type_intersection():
    # docs/json-schema.md#allof-and-type — allOf applies set intersection to type
    schema = SchemaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        all_of=[
            SchemaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/0'),
                type_={DataType.INTEGER, DataType.STRING},
            ),
            SchemaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/1'),
                type_={DataType.INTEGER, DataType.BOOLEAN},
            ),
        ],
    )

    result = schema.normalize_model()

    assert result == SchemaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        type_={DataType.INTEGER},
    )


def test_normalize_nested_allof():
    # docs/json-schema.md#nested-allof — nested allOf is flattened into a single allOf
    root = Stack.from_str('#/components/schemas/obj')
    schema = SchemaModel(
        stack=root,
        all_of=[
            SchemaModel(
                stack=root.push('allOf/0'),
                all_of=[
                    SchemaModel(
                        stack=root.push('allOf/0'),
                        type_={DataType.INTEGER},
                    ),
                    SchemaModel(
                        stack=root.push('allOf/1'),
                        ge=10.0,
                    ),
                ],
            ),
            SchemaModel(
                stack=root.push('allOf/1'),
                multiple_of=2,
            ),
        ],
    )

    result = schema.normalize_model()

    assert result == SchemaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        type_={DataType.INTEGER},
        ge=10.0,
        multiple_of=2,
    )


def test_normalize_allof_scalar_constraints():
    # docs/json-schema.md#allof-and-scalar-constraints — most restrictive value wins: max for ge/gt, min for le/lt
    schema = SchemaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        type_={DataType.INTEGER},
        all_of=[
            SchemaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/0'),
                ge=10.0,
                le=30.0,
            ),
            SchemaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/1'),
                ge=5.0,
                le=20.0,
            ),
        ],
    )

    result = schema.normalize_model()

    assert result == SchemaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        type_={DataType.INTEGER},
        ge=10.0,
        le=20.0,
    )


def test_normalize_single_anyof():
    schema = SchemaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        any_of=[
            SchemaModel(
                stack=Stack.from_str('#/components/schemas/obj/anyOf/0'),
                type_={DataType.OBJECT},
                properties={
                    'id': SchemaModel(
                        stack=Stack.from_str('#/components/schemas/obj/anyOf/0/properties/id'), type_={DataType.STRING}
                    )
                },
            )
        ],
    )

    schema = schema.normalize_model()

    expected = SchemaModel(
        stack=Stack.from_str('#/components/schemas/obj/anyOf/0'),
        type_={DataType.OBJECT},
        properties={
            'id': SchemaModel(
                stack=Stack.from_str('#/components/schemas/obj/anyOf/0/properties/id'),
                type_={DataType.STRING},
            )
        },
    )

    assert schema == expected


def test_normalize_allof_bottom_type_member_returns_none():
    # If any allOf member is a bottom type (None), the whole schema is unsatisfiable
    schema = SchemaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        all_of=[
            SchemaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/0'),
                type_={DataType.INTEGER},
            ),
            None,
        ],
    )

    assert schema.normalize_model() is None


def test_normalize_allof_contradicting_return_none():
    # If any allOf member is a bottom type (None), the whole schema is unsatisfiable
    schema = SchemaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        type_={DataType.STRING},
        all_of=[
            SchemaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/0'),
                type_={DataType.INTEGER},
            ),
        ],
    )

    assert schema.normalize_model() is None
