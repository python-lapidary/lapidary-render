from unittest import TestCase

from lapidary.runtime import ParamLocation, openapi
from lapidary.runtime.model import from_type
from lapidary.runtime.model.refs import get_resolver
from lapidary.runtime.model.type_hint import TypeHint, UnionTypeHint
from lapidary.runtime.module_path import ModulePath

from lapidary.render.model.attribute import AttributeModel
from lapidary.render.model.attribute_annotation import AttributeAnnotationModel
from lapidary.render.model.operation_function import get_operation_func
from lapidary.render.model.request_body import get_request_body_module
from lapidary.render.model.response_body import get_response_body_module
from lapidary.render.model.schema_class_model import SchemaClass
from lapidary.render.model.schema_module import SchemaModule

str_schema = schema = openapi.Schema(type=openapi.Type.string)
model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='Lapidary test schema', version='1.0.0'),
    paths=openapi.Paths(**{
        '/simple-response/': openapi.PathItem(
            get=openapi.Operation(
                operationId='get_simple_response',
                responses=openapi.Responses(**{
                    '200': openapi.Response(
                        description='test response',
                        content={'application/json': openapi.MediaType(
                            schema=str_schema,
                        )}
                    )
                })
            ),
        ),
        '/schema-response/': openapi.PathItem(
            get=openapi.Operation(
                operationId='get_schema_response',
                responses=openapi.Responses(**{
                    '200': openapi.Response(
                        description='test response',
                        content={'application/json': openapi.MediaType(
                            schema=openapi.Schema(
                                type=openapi.Type.object,
                                properties=dict(
                                    a=str_schema,
                                    b=str_schema,
                                ),
                                additionalProperties=False,
                            ),
                        )}
                    )
                })
            ),
        ),
        '/schema-request/': openapi.PathItem(
            get=openapi.Operation(
                operationId='get_schema_request',
                responses=openapi.Responses(
                    default=openapi.Response(
                        description=''
                    )
                ),
                requestBody=openapi.RequestBody(
                    content={'application/json': openapi.MediaType(
                        schema=openapi.Schema(
                            type=openapi.Type.object,
                            properties=dict(
                                a=str_schema,
                                b=str_schema,
                            ),
                            additionalProperties=False,
                        ),
                    )}
                ),
            ),
        ),
        '/ignored-header/': openapi.PathItem(
            get=openapi.Operation(
                operationId='ignored_header',
                responses=openapi.Responses(
                    default=openapi.Response(
                        description=''
                    )
                ),
                parameters=[
                    openapi.Parameter(
                        name='accept',
                        in_=ParamLocation.header.value,
                    )
                ]
            ),
        ),
    }))

resolve = get_resolver(model, 'lapidary_test')
module_path = ModulePath('lapidary_test')
union_str_absent = UnionTypeHint.of(
    from_type(str),
    TypeHint.from_str('lapidary.runtime.absent:Absent')
)
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

        mod = get_response_body_module(model.paths['/schema-response/'].get, module_path, resolve)
        # pp(mod)

        self.assertEqual(expected, mod)

    def test_request_body_schema_class(self):
        mod = get_request_body_module(model.paths['/schema-request/'].get, module_path, resolve)

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
        op_def = model.paths['/ignored-header/'].get
        op_model = get_operation_func(op_def, module_path, resolve)
        self.assertEqual([], op_model.params)
