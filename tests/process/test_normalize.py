from openapi_pydantic.v3.v3_1 import DataType

from lapidary_render.model.metamodel import MetaModel
from lapidary_render.model.stack import Stack


def test_normalize_allof_type_intersection():
    # docs/json-schema.md#allof-and-type — allOf applies set intersection to type
    schema = MetaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        all_of=[
            MetaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/0'),
                type_={DataType.INTEGER, DataType.STRING},
            ),
            MetaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/1'),
                type_={DataType.INTEGER, DataType.BOOLEAN},
            ),
        ],
    )

    result = schema.normalize_model()

    assert result == MetaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        type_={DataType.INTEGER},
    )


def test_normalize_nested_allof():
    # docs/json-schema.md#nested-allof — nested allOf is flattened into a single allOf
    root = Stack.from_str('#/components/schemas/obj')
    schema = MetaModel(
        stack=root,
        all_of=[
            MetaModel(
                stack=root.push('allOf/0'),
                all_of=[
                    MetaModel(
                        stack=root.push('allOf/0'),
                        type_={DataType.INTEGER},
                    ),
                    MetaModel(
                        stack=root.push('allOf/1'),
                        ge=10.0,
                    ),
                ],
            ),
            MetaModel(
                stack=root.push('allOf/1'),
                multiple_of=2,
            ),
        ],
    )

    result = schema.normalize_model()

    assert result == MetaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        type_={DataType.INTEGER},
        ge=10.0,
        multiple_of=2,
    )


def test_normalize_allof_scalar_constraints():
    # docs/json-schema.md#allof-and-scalar-constraints — most restrictive value wins: max for ge/gt, min for le/lt
    schema = MetaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        type_={DataType.INTEGER},
        all_of=[
            MetaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/0'),
                ge=10.0,
                le=30.0,
            ),
            MetaModel(
                stack=Stack.from_str('#/components/schemas/obj/allOf/1'),
                ge=5.0,
                le=20.0,
            ),
        ],
    )

    result = schema.normalize_model()

    assert result == MetaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        type_={DataType.INTEGER},
        ge=10.0,
        le=20.0,
    )


def test_normalize_single_anyof():
    schema = MetaModel(
        stack=Stack.from_str('#/components/schemas/obj'),
        any_of=[
            MetaModel(
                stack=Stack.from_str('#/components/schemas/obj/anyOf/0'),
                type_={DataType.OBJECT},
                properties={
                    'id': MetaModel(
                        stack=Stack.from_str('#/components/schemas/obj/anyOf/0/properties/id'), type_={DataType.STRING}
                    )
                },
            )
        ],
    )

    schema = schema.normalize_model()

    expected = MetaModel(
        stack=Stack.from_str('#/components/schemas/obj/anyOf/0'),
        type_={DataType.OBJECT},
        properties={
            'id': MetaModel(
                stack=Stack.from_str('#/components/schemas/obj/anyOf/0/properties/id'),
                type_={DataType.STRING},
            )
        },
    )

    assert schema == expected
