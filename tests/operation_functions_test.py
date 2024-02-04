from unittest import TestCase

import yaml
from lapidary.render.model import openapi
from lapidary.render.model.attribute import AttributeModel
from lapidary.render.model.attribute_annotation import AttributeAnnotationModel
from lapidary.render.model.operation_function import get_operation_func
from lapidary.render.model.python.module_path import ModulePath
from lapidary.render.model.python.type_hint import GenericTypeHint, TypeHint
from lapidary.render.model.refs import get_resolver
from lapidary.render.model.request_body import get_request_body_module
from lapidary.render.model.response_body import get_response_body_module
from lapidary.render.model.schema_class_model import SchemaClass
from lapidary.render.model.schema_module import SchemaModule

with open('operation_functions.yaml', 'r') as doc_file:
    doc = yaml.safe_load(doc_file)
model = openapi.OpenApiModel.model_validate(doc)


resolve = get_resolver(model, 'lapidary_test')
module_path = ModulePath('lapidary_test')
union_str_absent = GenericTypeHint.union_of((
    TypeHint.from_type(str),
    TypeHint.from_str('lapidary.runtime.absent:Absent')
))
common_attributes = [
    AttributeModel(
        name='a',
        annotation=AttributeAnnotationModel(
            type=union_str_absent,
            field_props={},
            default='lapidary.runtime.absent.ABSENT',
        ),
    ),
    AttributeModel(
        name='b',
        annotation=AttributeAnnotationModel(
            type=union_str_absent,
            field_props={},
            default='lapidary.runtime.absent.ABSENT',
        ),
    )
]


class OperationResponseTest(TestCase):
    def test_response_body_schema_model(self):
        expected = SchemaModule(
            path=module_path,
            imports=[
                'lapidary.runtime.absent',
            ],
            body=[SchemaClass(
                class_name='Response',
                base_type=TypeHint.from_str('pydantic:BaseModel'),
                attributes=common_attributes
            )]
        )

        mod = get_response_body_module(model.paths.model_extra['/schema-response/'].get, module_path, resolve)
        # pp(mod)

        self.assertEqual(expected, mod)

    def test_request_body_schema_class(self):
        mod = get_request_body_module(model.paths.model_extra['/schema-request/'].get, module_path, resolve)

        expected = SchemaModule(
            path=module_path,
            imports=[
                'lapidary.runtime.absent',
            ],
            body=[SchemaClass(
                class_name='GetSchemaRequestRequest',
                base_type=TypeHint.from_str('pydantic:BaseModel'),
                attributes=common_attributes
            )]
        )

        self.assertEqual(expected, mod)

    def test_ignored_header(self):
        op_def = model.paths.model_extra['/ignored-header/'].get
        op_model = get_operation_func(op_def, module_path, resolve)
        self.assertEqual([], op_model.params)
