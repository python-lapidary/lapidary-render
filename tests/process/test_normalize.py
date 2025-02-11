from openapi_pydantic.v3.v3_0 import DataType

from lapidary.render.model.metamodel import MetaModel
from lapidary.render.model.stack import Stack


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
