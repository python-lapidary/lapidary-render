import logging
from collections.abc import Mapping
from pathlib import Path

import pytest
import ruamel.yaml

from lapidary.render import json_pointer
from lapidary.render.model import OpenApi30Converter, openapi, python, stack

logging.basicConfig()
logging.getLogger('lapidary').setLevel(logging.DEBUG)


@pytest.fixture
def document() -> openapi.OpenApiModel:
    doc_text = (Path(__file__).parent.parent / 'e2e/init/petstore/src/openapi/openapi.json').read_text()
    return openapi.OpenApiModel.model_validate_json(doc_text)


@pytest.fixture
def doc_dummy() -> openapi.OpenApiModel:
    doc_text = (Path(__file__).parent.parent / 'e2e/init/dummy/dummy.yaml').read_text()
    yaml = ruamel.yaml.YAML(typ='safe')
    return openapi.OpenApiModel.model_validate(yaml.load(doc_text))


def test_schema_str(document: openapi.OpenApiModel) -> None:
    converter = OpenApi30Converter(python.ModulePath('petstore', False), document, None)
    operations: Mapping[str, openapi.Operation] = document.paths.paths['/user/login'].model_extra

    responses = converter.process_responses(
        operations['get'].responses, stack.Stack(('#', 'paths', '/user/login', 'get', 'responses'))
    )

    assert responses['200']['application/json'] == python.TypeHint(
        module='petstore.paths.u_luseru_llogin.get.responses.u_o00', name='Response'
    )
    assert converter.schema_converter.schema_modules == []


def test_schema_array(document: openapi.OpenApiModel) -> None:
    converter = OpenApi30Converter(python.ModulePath('petstore', False), document, None)
    operations: Mapping[str, openapi.Operation] = document.paths.paths['/user/createWithList'].model_extra

    request = converter.process_request_body(
        operations['post'].request_body, stack.Stack(('#', 'paths', '/user/createWithList', 'post', 'requestBody'))
    )

    assert request['application/json'] == python.GenericTypeHint(
        module='builtins', name='list', args=(python.TypeHint.from_str('petstore.components.schemas.User.schema:User'),)
    )
    assert converter.schema_converter.schema_modules[0].body[0].class_name == 'User'


def test_property_schema(doc_dummy: openapi.OpenApiModel) -> None:
    converter = OpenApi30Converter(python.ModulePath('dummy', False), doc_dummy, None)
    operations: Mapping[str, openapi.Operation] = doc_dummy.paths.paths['/test/'].model_extra

    schema = converter.schema_converter.process_schema(
        operations['get'].parameters[1].schema_,
        stack.Stack(('#', 'paths', json_pointer.encode_json_pointer('/test/'), 'get', 'parameters', '1', 'schema')),
    )

    assert schema == python.TypeHint.from_str('dummy.paths.u_ltestu_l.get.parameters.u_n.schema.schema:schema')
