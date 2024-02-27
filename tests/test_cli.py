import pathlib
import unittest
from unittest.mock import Mock

from typer.testing import CliRunner


@unittest.mock.patch('rybak.TreeTemplate')
def test_init_save_copies_document(monkeypatch, tmp_path: pathlib.Path) -> None:
    runner = CliRunner()
    output = tmp_path / 'output'
    from lapidary.render.cli import app

    with unittest.mock.patch('rybak.TreeTemplate') as mock:
        result = runner.invoke(app, ('init', '--save', 'petstore.json', str(output), 'petstore'))
    if result.exception:
        raise result.exception
    mock().render.assert_called()
    assert result.exit_code == 0
    assert (output / 'src/openapi/petstore.json').is_file()


def test_init_dosnt_copy_document(tmp_path: pathlib.Path) -> None:
    runner = CliRunner()
    output = tmp_path / 'output'
    from lapidary.render.cli import app

    with unittest.mock.patch('rybak.TreeTemplate') as mock:
        result = runner.invoke(app, ('init', 'petstore.json', str(output), 'petstore'))
    if result.exception:
        raise result.exception
    assert result.exit_code == 0
    mock().render.assert_called()
    assert not (output / 'src/openapi/petstore.json').is_file()
