import logging
import typing
from pathlib import Path

import pytest
import ruamel.yaml
from openapi_pydantic.v3.v3_1 import schema as schema31

from lapidary.render import runtime
from lapidary.render.model import conv_openapi, conv_schema, metamodel, openapi, python, stack

logging.basicConfig()
logging.getLogger('lapidary').setLevel(logging.DEBUG)

yaml = ruamel.yaml.YAML(typ='safe')


@pytest.fixture
def document() -> openapi.OpenAPI:
    doc_text = (Path(__file__).parent.parent / 'e2e/init/petstore/src/openapi/openapi.yaml').read_text()
    return openapi.OpenAPI.model_validate(yaml.load(doc_text))


@pytest.fixture
def doc_dummy() -> openapi.OpenAPI:
    doc_text = (Path(__file__).parent.parent / 'e2e/init/dummy/dummy.yaml').read_text()
    return openapi.OpenAPI.model_validate(yaml.load(doc_text))


def test_schema_str(document: openapi.OpenAPI) -> None:
    converter = conv_openapi.OpenApi30Converter(python.ModulePath('petstore', False), document, None)
    operations: openapi.PathItem = document.paths.paths['/user/login']

    responses = converter.process_responses(
        operations.get.responses, stack.Stack(('#', 'paths', '/user/login', 'get', 'responses'))
    )

    assert responses['200'].content['application/json'] == python.AnnotatedType(python.NameRef.from_type(str))
    assert converter.schema_converter.schema_modules == []


def test_schema_array(document: openapi.OpenAPI) -> None:
    converter = conv_openapi.OpenApi30Converter(python.ModulePath('petstore', False), document, None)
    operations: openapi.PathItem = document.paths.paths['/user/createWithList']

    request = converter.process_request_body(
        operations.post.requestBody, stack.Stack(('#', 'paths', '/user/createWithList', 'post', 'requestBody'))
    )

    assert request['application/json'] == python.list_of(
        python.AnnotatedType(python.NameRef(module='petstore.components.schemas.User.schema', name='User'))
    )

    assert converter.schema_converter.schema_modules[0].body[0].name == 'User'


def test_property_schema(doc_dummy: openapi.OpenAPI) -> None:
    converter = conv_openapi.OpenApi30Converter(python.ModulePath('dummy', False), doc_dummy, None)
    operations: openapi.PathItem = doc_dummy.paths.paths['/test/']

    schema: metamodel.MetaModel = converter.schema_converter.process_type_schema(
        operations.get.parameters[1].param_schema,
        stack.Stack.from_str('#/paths/~1test~1/get/parameters/1/schema'),
    )

    assert schema.as_annotation('dummy') == python.AnnotatedType(
        python.NameRef('dummy.paths.u_ltestu_l.get.parameters.u_n.schema.schema', 'schema')
    )
    print(list(schema.as_types('package')))


def test_int_one_of():
    doc = openapi.OpenAPI(
        info=openapi.Info(
            title='test oneOf',
            version='1.0.0',
        ),
        paths=openapi.Paths(paths={}),
        components=openapi.Components(
            schemas={
                'myschema': openapi.Schema(
                    type=openapi.DataType.INTEGER,
                    oneOf=[
                        openapi.Schema(maximum=10),
                        openapi.Schema(minimum=20),
                    ],
                )
            }
        ),
    )
    converter = conv_schema.OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_schema(
        doc.components.schemas['myschema'], stack.Stack(('#', 'components', 'schemas', 'myschema'))
    )
    print(model)
    print(model.as_annotation('root'))


@pytest.mark.skip('Not implemented')
def test_int_one_of_recurrent():
    doc = openapi.OpenAPI(
        info=openapi.Info(
            title='test oneOf',
            version='1.0.0',
        ),
        paths=openapi.Paths(paths={}),
        components=openapi.Components(
            schemas={
                'myschema': openapi.Schema(
                    type=openapi.DataType.OBJECT,
                    properties={
                        'prop1': openapi.Schema(
                            oneOf=[
                                openapi.Schema(
                                    maximum=10,
                                    type=openapi.DataType.INTEGER,
                                ),
                                openapi.Reference[openapi.Schema](ref='#/components/schemas/myschema'),
                            ]
                        )
                    },
                )
            }
        ),
    )
    converter = conv_schema.OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_type_schema(
        doc.components.schemas['myschema'],
        stack.Stack(('#', 'components', 'schemas', 'myschema')),
    )
    from pprint import pprint

    pprint(model)
    pprint(model.as_annotation('root'))
    pprint(converter.schema_modules)


def mk_schemas_doc(title: str, **schemas: openapi.Schema) -> openapi.OpenAPI:
    return openapi.OpenAPI(
        info=openapi.Info(
            title=title,
            version='1.0.0',
        ),
        paths=openapi.Paths(paths={}),
        components=openapi.Components(schemas=schemas),
    )


def test_one_of_mix():
    doc = mk_schemas_doc(
        'test oneOf',
        myschema=openapi.Schema(
            type=openapi.DataType.INTEGER,
            oneOf=[
                openapi.Schema(maximum=10),
                openapi.Schema(minimum=20),
                openapi.Schema(maxLength=10),
            ],
        ),
    )
    converter = conv_schema.OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_schema(
        doc.components.schemas['myschema'], stack.Stack(('#', 'components', 'schemas', 'myschema'))
    )
    print(model)


def test_enum_limits_type():
    doc = mk_schemas_doc(
        'test enums',
        myschema=openapi.Schema(
            enum=[True, False, 'FileNotFound'],
        ),
    )
    converter = conv_schema.OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    stack_ = stack.Stack(('#', 'components', 'schemas', 'myschema'))
    model = converter.process_schema(doc.components.schemas['myschema'], stack_)
    assert model == metamodel.MetaModel(
        stack=stack_.push('schema', 'myschema'),
        type_={schema31.DataType.BOOLEAN, schema31.DataType.STRING},
        enum={True, False, 'FileNotFound'},
    )


def test_process_anyof_objects():
    doc = mk_schemas_doc(
        'test enums',
        object1=openapi.Schema(
            type=openapi.DataType.OBJECT,
            properties={
                'str': openapi.Schema(type=openapi.DataType.STRING),
            },
        ),
        object2=openapi.Schema(
            type=openapi.DataType.OBJECT,
            properties={
                'int': openapi.Schema(
                    type=openapi.DataType.INTEGER,
                ),
            },
        ),
        myschema=openapi.Schema(
            anyOf=[
                openapi.Reference(ref='#/components/schemas/object1'),
                openapi.Reference(ref='#/components/schemas/object2'),
                openapi.Schema(
                    type=openapi.DataType.INTEGER,
                    maximum=20,
                    nullable=True,
                ),
            ]
        ),
    )
    converter = conv_schema.OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_type_schema(
        doc.components.schemas['myschema'], stack.Stack(('#', 'components', 'schemas', 'myschema'))
    )

    # check normalized model
    assert model == metamodel.MetaModel(
        stack=stack.Stack(('#', 'components', 'schemas', 'myschema', 'schema', 'myschema')),
        type_=metamodel._all_types(),
        any_of=[
            metamodel.MetaModel(
                stack=stack.Stack(('#', 'components', 'schemas', 'object1', 'schema', 'object1')),
                type_={schema31.DataType.OBJECT},
                properties={
                    'str': metamodel.MetaModel(
                        stack=stack.Stack(
                            ('#', 'components', 'schemas', 'object1', 'properties', 'str', 'schema', 'str')
                        ),
                        type_={openapi.DataType.STRING},
                    ),
                },
            ),
            metamodel.MetaModel(
                stack=stack.Stack(('#', 'components', 'schemas', 'object2', 'schema', 'object2')),
                type_={schema31.DataType.OBJECT},
                properties={
                    'int': metamodel.MetaModel(
                        stack=stack.Stack(
                            ('#', 'components', 'schemas', 'object2', 'properties', 'int', 'schema', 'int')
                        ),
                        type_={openapi.DataType.INTEGER},
                    ),
                },
            ),
            metamodel.MetaModel(
                stack=stack.Stack(('#', 'components', 'schemas', 'myschema', 'schema', 'AnyOf2')),
                type_={schema31.DataType.INTEGER},
                ge=20.0,
            ),
        ],
    )

    assert model.as_annotation('package') == python.AnnotatedType(
        python.type_hint._UNION,
        (
            python.AnnotatedType(python.NameRef.from_type(int), ge=20),
            python.AnnotatedType(python.NameRef('package.components.schemas.object1.schema', 'object1')),
            python.AnnotatedType(python.NameRef('package.components.schemas.object2.schema', 'object2')),
        ),
    )

    assert list(model.as_types('root')) == [
        python.SchemaClass(
            'object1',
            runtime.ModelBase,
            True,
            None,
            [
                python.AnnotatedVariable(
                    'str',
                    python.AnnotatedType.from_type(
                        typing.Union, (python.AnnotatedType.from_type(str), python.NoneMetaType)
                    ),
                    False,
                    None,
                )
            ],
        ),
        python.SchemaClass(
            'object2',
            runtime.ModelBase,
            True,
            None,
            [
                python.AnnotatedVariable(
                    'int',
                    python.AnnotatedType.from_type(
                        typing.Union, (python.AnnotatedType.from_type(int), python.NoneMetaType)
                    ),
                    False,
                    None,
                )
            ],
        ),
    ]


def test_process_default_object():
    doc = mk_schemas_doc(
        'test enums',
        obj=openapi.Schema(
            type=openapi.DataType.OBJECT,
        ),
    )
    converter = conv_schema.OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_type_schema(
        doc.components.schemas['obj'], stack.Stack(('#', 'components', 'schemas', 'myschema'))
    )
    assert model.as_annotation('package') == runtime.JsonObject


def test_process_default_schema():
    doc = mk_schemas_doc(
        'test enums',
        obj=openapi.Schema(),
    )
    converter = conv_schema.OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_type_schema(
        doc.components.schemas['obj'], stack.Stack(('#', 'components', 'schemas', 'myschema'))
    )
    assert model is not None
    assert list(model.as_types('package')) == []
    assert model.as_annotation('package') == runtime.JsonValue


def test_process_union_object_int():
    doc = mk_schemas_doc(
        'test enums',
        schema1=openapi.Schema(
            type=openapi.DataType.OBJECT,
            properties={
                'prop1': openapi.Schema(
                    type=openapi.DataType.STRING,
                )
            },
            required=['prop1'],
        ),
        union=openapi.Schema(
            anyOf=[
                openapi.Reference(ref='#/components/schemas/schema1'),
                openapi.Schema(
                    type=openapi.DataType.INTEGER,
                ),
            ]
        ),
    )
    converter = conv_schema.OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_type_schema(
        doc.components.schemas['union'], stack.Stack(('#', 'components', 'schemas', 'union'))
    )
    assert list(model.as_types('package')) == [
        python.SchemaClass(
            'schema1',
            python.NameRef('lapidary.runtime', 'ModelBase'),
            True,
            fields=[
                python.AnnotatedVariable(
                    'prop1',
                    python.AnnotatedType.from_type(str),
                    True,
                    None,
                )
            ],
        )
    ]
    assert model.as_annotation('package') == python.AnnotatedType(
        python.NameRef('typing', 'Union'),
        (
            python.AnnotatedType(python.NameRef('builtins', 'int')),
            python.AnnotatedType(python.NameRef('package.components.schemas.schema1.schema', 'schema1')),
        ),
    )
