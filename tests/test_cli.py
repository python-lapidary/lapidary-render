import pathlib

import anyio
import pytest
from asyncclick.testing import CliRunner

from lapidary.render.config import load_config

source = pathlib.Path(__file__).relative_to(pathlib.Path.cwd()).parent / 'e2e/init/petstore/src/openapi/openapi.json'


@pytest.mark.asyncio
async def test_init_save_copies_document(monkeypatch, tmp_path: pathlib.Path) -> None:
    runner = CliRunner()
    output = tmp_path / 'output'
    from lapidary.render.cli import app

    result = await runner.invoke(app, ('init', '--save', str(source), str(output), 'petstore'))
    if result.exception:
        raise result.exception
    assert result.exit_code == 0
    assert (output / 'src/openapi/openapi.json').is_file()

    config = await load_config(anyio.Path(output))
    assert config.origin is None
    assert config.document_path == 'src/openapi/openapi.json'


@pytest.mark.asyncio
async def test_init_doesnt_copy_document(tmp_path: pathlib.Path) -> None:
    runner = CliRunner()
    output = tmp_path / 'output'
    from lapidary.render.cli import app

    result = await runner.invoke(app, ('init', str(source), str(output), 'petstore'))
    if result.exception:
        raise result.exception
    assert result.exit_code == 0
    assert not (output / 'src/openapi/petstore.json').is_file()

    config = await load_config(anyio.Path(output))
    assert config.document_path == str(await anyio.Path.cwd() / source)


@pytest.mark.asyncio
async def test_init_url_saves_origin(tmp_path: pathlib.Path) -> None:
    from lapidary.render.cli import app

    runner = CliRunner()
    output = tmp_path / 'output'
    source = 'https://petstore3.swagger.io/api/v3/openapi.json'
    result = await runner.invoke(app, ('init', str(source), str(output), 'petstore'))
    if result.exit_code != 0:
        print(result.output)
        print(result.exception)

    assert result.exit_code == 0

    config = await load_config(anyio.Path(output))
    assert str(config.origin) == source
    assert config.document_path is None
