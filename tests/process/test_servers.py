from pathlib import Path

import pytest
import ruamel.yaml

from lapidary.render import model
from lapidary.render.model import openapi, python
from lapidary.render.model.stack import Stack

yaml = ruamel.yaml.YAML(typ='safe')

yaml_home = Path(__file__).parent / 'servers'
test_files = [
    (yaml_home / 'none.yaml', '/'),
    (yaml_home / 'empty.yaml', None),
    (yaml_home / 'single.yaml', 'https://petstore3.swagger.io/api/v3'),
    (yaml_home / 'single-vars.yaml', 'https://petstore3.production.swagger.io/api/v3'),
]


@pytest.mark.parametrize('document_path, expected', test_files)
def test_servers(document_path: Path, expected: str | None):
    doc_text = document_path.read_text()
    document = openapi.OpenAPI.model_validate(yaml.load(doc_text))

    converter = model.OpenApi30Converter(python.ModulePath('package', False), document, None)
    converter.process_servers(document.servers, Stack(('#', 'servers')))
    assert converter.target.client.body.init_method.base_url == expected
