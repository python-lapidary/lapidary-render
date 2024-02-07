from unittest import TestCase

import yaml
from lapidary.render.model import openapi, python
from lapidary.render.model.operation_function import get_operation_func
from lapidary.render.model.refs import get_resolver
from lapidary.render.model.request_body import get_request_body_module
from lapidary.render.model.response_body import get_response_body_module

with open('operation_functions.yaml') as doc_file:
    doc = yaml.safe_load(doc_file)
model = openapi.OpenApiModel.model_validate(doc)


resolve = get_resolver(model, 'lapidary_test')
module_path = python.ModulePath('lapidary_test')
union_str_absent = python.GenericTypeHint.union_of(
    (python.TypeHint.from_type(str), python.TypeHint.from_str('lapidary.runtime.absent:Absent'))
)
common_attributes = [
    python.AttributeModel(
        name='a',
        annotation=python.AttributeAnnotationModel(
            type=union_str_absent,
            field_props={},
            default='lapidary.runtime.absent.ABSENT',
        ),
    ),
    python.AttributeModel(
        name='b',
        annotation=python.AttributeAnnotationModel(
            type=union_str_absent,
            field_props={},
            default='lapidary.runtime.absent.ABSENT',
        ),
    ),
]


class OperationResponseTest(TestCase):
    def test_response_body_schema_model(self):
        expected = python.SchemaModule(
            path=module_path,
            imports=[
                'lapidary.runtime.absent',
            ],
            body=[
                python.SchemaClass(
                    class_name='Response',
                    base_type=python.TypeHint.from_str('pydantic:BaseModel'),
                    attributes=common_attributes,
                )
            ],
        )

        mod = get_response_body_module(model.paths.paths['/schema-response/'].get, module_path, resolve)

        self.assertEqual(expected, mod)

    def test_request_body_schema_class(self):
        mod = get_request_body_module(model.paths.paths['/schema-request/'].get, module_path, resolve)

        expected = python.SchemaModule(
            path=module_path,
            imports=[
                'lapidary.runtime.absent',
            ],
            body=[
                python.SchemaClass(
                    class_name='GetSchemaRequestRequest',
                    base_type=python.TypeHint.from_str('pydantic:BaseModel'),
                    attributes=common_attributes,
                )
            ],
        )

        self.assertEqual(expected, mod)

    def test_ignored_header(self):
        op_def = model.paths.paths['/ignored-header/'].get
        op_model = get_operation_func(op_def, module_path, resolve)
        self.assertEqual([], op_model.params)
