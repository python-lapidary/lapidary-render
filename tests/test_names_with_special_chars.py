import logging
from unittest import TestCase

import yaml
from lapidary.render.model import openapi, python
from lapidary.render.model.refs import get_resolver
from lapidary.render.model.schema_class import get_schema_classes
from lapidary.render.model.schema_module import get_schema_module, get_schema_modules

logging.getLogger('lapidary').setLevel(logging.DEBUG)


module_path = python.ModulePath('lapidary_test')


class NamingTest(TestCase):
    def test_name_with_alias(self):
        with open('name_with_alias.yaml') as document_file:
            model = openapi.OpenApiModel.model_validate(yaml.safe_load(document_file))
        resolve = get_resolver(model, 'lapidary_test')

        expected = python.SchemaModule(
            path=module_path,
            imports=list(),
            body=[
                python.SchemaClass(
                    class_name='NonSpaceNameRandomProperty',
                    base_type=python.TypeHint.from_str('pydantic:BaseModel'),
                    attributes=[
                        python.AttributeModel(
                            'key',
                            python.AttributeAnnotationModel(python.TypeHint.from_type(str), {}),
                        ),
                    ],
                ),
                python.SchemaClass(
                    has_aliases=True,
                    class_name='NonSpaceName',
                    base_type=python.TypeHint.from_str('pydantic:BaseModel'),
                    attributes=[
                        python.AttributeModel(
                            'random_property',
                            python.AttributeAnnotationModel(
                                python.TypeHint.from_str('lapidary_test:NonSpaceNameRandomProperty'),
                                {
                                    'alias': "'random property'",
                                },
                            ),
                        ),
                    ],
                ),
            ],
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
        model = openapi.Schema(enum=[None], nullable=True, lapidary_names={None: 'null'})
        result = [c for c in get_schema_classes(model, 'test', module_path, None)]
        self.assertEqual('null', result[0].attributes[0].name)
