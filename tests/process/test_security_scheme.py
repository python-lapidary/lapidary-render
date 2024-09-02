from pathlib import Path

import pytest
import ruamel.yaml

from lapidary.render import model
from lapidary.render.model import openapi, python
from lapidary.render.model.stack import Stack


@pytest.fixture()
def yaml():
    return ruamel.yaml.YAML(typ='safe')


@pytest.mark.parametrize('path', (Path(__file__).parent / 'security_schemes').glob('*'))
def test_process_security_schemes(yaml: ruamel.yaml.YAML, path: Path):
    document = openapi.OpenAPI.model_validate(yaml.load(path.read_text()))

    converter = model.OpenApi30Converter(python.ModulePath('package', False), document, None)
    for name, security_scheme in document.components.securitySchemes.items():
        converter.process_security_scheme(security_scheme, Stack(('#', 'components', 'securitySchemes', name)))

    assert converter.target.security_schemes['api_key_headerApiKey'] == python.ApiKeyAuth(
        name='headerApiKey',
        python_name='headerApiKey',
        key='Authorization',
        location=python.ParamLocation.HEADER,
        format='{}',
    )
    assert converter.target.security_schemes['api_key_cookieApiKey'] == python.ApiKeyAuth(
        name='cookieApiKey',
        python_name='cookieApiKey',
        key='Authorization',
        location=python.ParamLocation.COOKIE,
        format='{}',
    )
