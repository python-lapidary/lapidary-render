import pathlib
import unittest
from unittest.mock import Mock

import pytest
from asyncclick.testing import CliRunner

source = pathlib.Path(__file__).relative_to(pathlib.Path.cwd()).parent / 'e2e/init/petstore/petstore.json'


@pytest.mark.asyncio
async def test_init_save_copies_document(monkeypatch, tmp_path: pathlib.Path) -> None:
    runner = CliRunner()
    output = tmp_path / 'output'
    from lapidary.render.cli import app

    with unittest.mock.patch('rybak.TreeTemplate') as mock:
        result = await runner.invoke(app, ('init', '--save', str(source), str(output), 'petstore'))
    if result.exception:
        raise result.exception
    mock().render.assert_called()
    assert result.exit_code == 0
    assert (output / 'src/openapi/petstore.json').is_file()


@pytest.mark.asyncio
async def test_init_doesnt_copy_document(tmp_path: pathlib.Path) -> None:
    runner = CliRunner()
    output = tmp_path / 'output'
    from lapidary.render.cli import app

    with unittest.mock.patch('rybak.TreeTemplate') as mock:
        result = await runner.invoke(app, ('init', str(source), str(output), 'petstore'))
    if result.exception:
        raise result.exception
    assert result.exit_code == 0
    mock().render.assert_called()
    assert not (output / 'src/openapi/petstore.json').is_file()
