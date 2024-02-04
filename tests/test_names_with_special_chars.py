import logging
from unittest import TestCase

import yaml
from lapidary.render.model import get_schema_modules, openapi
from lapidary.render.model.attribute import AttributeModel
from lapidary.render.model.attribute_annotation import AttributeAnnotationModel
from lapidary.render.model.python.module_path import ModulePath
from lapidary.render.model.python.type_hint import TypeHint
from lapidary.render.model.refs import get_resolver
from lapidary.render.model.schema_class import get_schema_classes
from lapidary.render.model.schema_class_model import SchemaClass
from lapidary.render.model.schema_module import SchemaModule, get_schema_module

logging.getLogger('lapidary').setLevel(logging.DEBUG)


module_path = ModulePath('lapidary_test')


class NamingTest(TestCase):
    def test_name_with_alias(self):
        with open('name_with_alias.yaml') as document_file:
            model = openapi.OpenApiModel.model_validate(yaml.safe_load(document_file))
        resolve = get_resolver(model, 'lapidary_test')

        expected = SchemaModule(
            path=module_path,
            imports=[
            ],
            body=[
                SchemaClass(
                    class_name='NonSpaceNameRandomProperty',
                    base_type=TypeHint.from_str('pydantic:BaseModel'),
                    attributes=[
                        AttributeModel(
                            'key',
                            AttributeAnnotationModel(TypeHint.from_type(str), {}),
                        ),
                    ],
                ),
                SchemaClass(
                    has_aliases=True,
                    class_name='NonSpaceName',
                    base_type=TypeHint.from_str('pydantic:BaseModel'),
                    attributes=[
                        AttributeModel(
                            'random_property',
                            AttributeAnnotationModel(
                                TypeHint.from_str('lapidary_test:NonSpaceNameRandomProperty'),
                                {
                                    'alias': "'random property'",
                                },
                            ),
                        ),
                    ],
                ),
            ]
        )

        mod = get_schema_module(model.components.schemas['NonSpaceName'], 'NonSpaceName', module_path, resolve)

        self.assertEqual(expected, mod)

    def test_name_with_space(self):
        with open('name_with_space.yaml') as doc_file:
            model = openapi.OpenApiModel.model_validate(yaml.safe_load(doc_file))
        resolve = get_resolver(model, 'lapidary_test')

        with self.assertRaises(ValueError):
            _ = [mod for mod in get_schema_modules(model, module_path, resolve)]

    def test_null_enum(self):
        model = openapi.Schema(
            enum=[None],
            nullable=True,
        )
        with self.assertRaises(ValueError):
            _ = [c for c in get_schema_classes(model, 'test', module_path, None)]

    def test_null_enum_with_alias(self):
        model = openapi.Schema(
            enum=[None],
            nullable=True,
            lapidary_names={
                None: 'null'
            }
        )
        result = [c for c in get_schema_classes(model, 'test', module_path, None)]
        self.assertEqual('null', result[0].attributes[0].name)
