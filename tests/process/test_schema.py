import logging
from pathlib import Path

import pytest
import ruamel.yaml

from lapidary.render.model import OpenApi30Converter, openapi, python, stack
from lapidary.render.model.conv_schema import OpenApi30SchemaConverter
from lapidary.render.model.metamodel import MetaModel
from lapidary.render.model.python import type_hint

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
    converter = OpenApi30Converter(python.ModulePath('petstore', False), document, None)
    operations: openapi.PathItem = document.paths.paths['/user/login']

    responses = converter.process_responses(
        operations.get.responses, stack.Stack(('#', 'paths', '/user/login', 'get', 'responses'))
    )

    assert responses['200'].content['application/json'] == python.AnnotatedType(python.NameRef.from_type(str))
    assert converter.schema_converter.schema_modules == []


def test_schema_array(document: openapi.OpenAPI) -> None:
    converter = OpenApi30Converter(python.ModulePath('petstore', False), document, None)
    operations: openapi.PathItem = document.paths.paths['/user/createWithList']

    request = converter.process_request_body(
        operations.post.requestBody, stack.Stack(('#', 'paths', '/user/createWithList', 'post', 'requestBody'))
    )

    assert request['application/json'] == python.list_of(
        python.AnnotatedType(python.NameRef(module='petstore.components.schemas.User.schema', name='User'))
    )

    assert converter.schema_converter.schema_modules[0].body[0].name == 'User'


def test_property_schema(doc_dummy: openapi.OpenAPI) -> None:
    converter = OpenApi30Converter(python.ModulePath('dummy', False), doc_dummy, None)
    operations: openapi.PathItem = doc_dummy.paths.paths['/test/']

    schema: MetaModel = converter.schema_converter.process_type_schema(
        operations.get.parameters[1].param_schema,
        stack.Stack.from_str('#/paths/~1test~1/get/parameters/1/schema'),
    )

    assert schema.as_annotation('dummy') == python.AnnotatedType(
        python.NameRef('dummy.paths.u_ltestu_l.get.parameters.u_n.schema.schema', 'schema')
    )
    print(schema.as_type('package'))


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
    converter = OpenApi30SchemaConverter(python.ModulePath('root'), doc)
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
    converter = OpenApi30SchemaConverter(python.ModulePath('root'), doc)
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
    converter = OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_schema(
        doc.components.schemas['myschema'], stack.Stack(('#', 'components', 'schemas', 'myschema'))
    )
    print(model)


def test_enums():
    doc = mk_schemas_doc(
        'test enums',
        myschema=openapi.Schema(
            enum=[True, False, 'FileNotFound'],
        ),
    )
    converter = OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_schema(
        doc.components.schemas['myschema'], stack.Stack(('#', 'components', 'schemas', 'myschema'))
    )
    print(model)


def test_process_anyof():
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
    converter = OpenApi30SchemaConverter(python.ModulePath('root'), doc)
    model = converter.process_type_schema(
        doc.components.schemas['myschema'], stack.Stack(('#', 'components', 'schemas', 'myschema'))
    )
    assert model is not None

    annotation = model.as_annotation('package')

    assert annotation == python.AnnotatedType(
        type_hint._UNION,
        (
            python.AnnotatedType(python.NameRef.from_type(int), ge=20),
            python.AnnotatedType(python.NameRef('package.components.schemas.myschema.schema', 'myschema')),
            python.NoneMetaType,
        ),
    )
