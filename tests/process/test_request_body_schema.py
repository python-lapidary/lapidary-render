from collections.abc import Mapping
from pathlib import Path

from lapidary.render.model import OpenApi30Converter
from lapidary.render.model.openapi import OpenApiModel, Operation
from lapidary.render.model.python import BuiltinTypeHint, ModulePath
from lapidary.render.model.stack import Stack


def test_request_body_schema() -> None:
    doc_text = (Path(__file__).parent.parent / 'petstore.json').read_text()
    doc = OpenApiModel.model_validate_json(doc_text)
    converter = OpenApi30Converter(ModulePath('petstore'), doc)
    operations: Mapping[str, Operation] = doc.paths.paths['/user/login'].model_extra

    assert converter.process_responses(
        operations['get'].responses, Stack(('#', 'paths', '/user/login', 'get', 'responses'))
    ) == BuiltinTypeHint.from_str('str')

    assert not converter.schema_converter.schema_modules
