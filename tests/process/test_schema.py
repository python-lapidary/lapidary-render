import logging
from collections.abc import Mapping
from pathlib import Path

import pytest

from lapidary.render.model import OpenApi30Converter, openapi, python, stack
from lapidary.runtime.http_consts import MIME_JSON

logging.basicConfig()
logging.getLogger('lapidary').setLevel(logging.DEBUG)


@pytest.fixture
def document() -> openapi.OpenApiModel:
    doc_text = (Path(__file__).parent.parent / 'petstore.json').read_text()
    return openapi.OpenApiModel.model_validate_json(doc_text)


def test_schema_str(document: openapi.OpenApiModel) -> None:
    converter = OpenApi30Converter(python.ModulePath('petstore'), document)
    operations: Mapping[str, openapi.Operation] = document.paths.paths['/user/login'].model_extra

    responses = converter.process_responses(
        operations['get'].responses, stack.Stack(('#', 'paths', '/user/login', 'get', 'responses'))
    )

    assert responses['200'][MIME_JSON] == python.BuiltinTypeHint.from_str('str')
    assert converter.schema_converter.schema_modules == []


def test_schema_array(document: openapi.OpenApiModel) -> None:
    converter = OpenApi30Converter(python.ModulePath('petstore'), document)
    operations: Mapping[str, openapi.Operation] = document.paths.paths['/user/createWithList'].model_extra

    request = converter.process_request_body(
        operations['post'].requestBody, stack.Stack(('#', 'paths', '/user/createWithList', 'post', 'requestBody'))
    )

    assert request[MIME_JSON] == python.GenericTypeHint(
        module='builtins', name='list', args=(python.TypeHint.from_str('petstore.components.schemas.User.schema:User'),)
    )
    assert converter.schema_converter.schema_modules[0].body[0].class_name == 'User'
