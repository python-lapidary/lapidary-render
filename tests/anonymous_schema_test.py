from unittest import TestCase

import yaml
from lapidary.render.model import openapi, python
from lapidary.render.model.refs import get_resolver
from lapidary.render.model.schema_class import get_schema_class, get_schema_classes
from lapidary.runtime import Absent

with open('anonymous_schema.yaml', 'r') as document_file:
    doc = yaml.safe_load(document_file)
model = openapi.OpenApiModel.model_validate(doc)


class Test(TestCase):
    def test_resolve_ref(self):
        a = get_schema_class(
            model.components.schemas['alice'],
            'alice',
            python.ModulePath('alice'),
            get_resolver(model, 'bob'),
        )
        schema = python.SchemaClass(
            class_name='alice',
            base_type=python.TypeHint.from_str('pydantic:BaseModel'),
            docstr=None,
            attributes=[python.AttributeModel(
                name='bob',
                annotation=python.AttributeAnnotationModel(
                    type=python.GenericTypeHint.union_of((python.TypeHint.from_type(str), python.TypeHint.from_type(Absent))),
                    field_props={},
                    style=None,
                    explode=None,
                    allowReserved=False,
                    default='lapidary.runtime.absent.ABSENT',
                ),
                deprecated=False
            )]
        )

        self.assertEqual(schema, a)

    def test_schema_type_name(self):
        classes = list(get_schema_classes(
            model.components.schemas['charlie'],
            'alice',
            python.ModulePath('test'),
            get_resolver(model, 'test'),
        ))
        class_names = [cls.class_name for cls in classes]
        self.assertEqual(class_names, ['FirstSchemaClass', 'SecondSchemaClass'])
