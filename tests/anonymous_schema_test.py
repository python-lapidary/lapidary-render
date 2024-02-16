from unittest import TestCase

import yaml

from lapidary.render.model import openapi, python
from lapidary.render.model.context import Context
from lapidary.render.model.schema_class import process_schema
from lapidary.runtime import Absent

with open('anonymous_schema.yaml') as document_file:
    doc = yaml.safe_load(document_file)
model = openapi.OpenApiModel.model_validate(doc)


class Test(TestCase):
    def test_resolve_ref(self):
        a = process_schema(Context(model, 'root_pkg'), model.components.schemas['alice'])
        schema = python.SchemaClass(
            class_name='alice',
            base_type=python.TypeHint.from_str('pydantic:BaseModel'),
            docstr=None,
            attributes=[
                python.AttributeModel(
                    name='bob',
                    annotation=python.AttributeAnnotationModel(
                        type=python.GenericTypeHint.union_of(
                            (python.TypeHint.from_type(str), python.TypeHint.from_type(Absent))
                        ),
                        field_props={},
                        style=None,
                        explode=None,
                        allowReserved=False,
                        default='lapidary.runtime.absent.ABSENT',
                    ),
                    deprecated=False,
                )
            ],
        )

        self.assertEqual(schema, a)
