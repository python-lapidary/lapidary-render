from pathlib import Path

from click.testing import CliRunner

from lapidary.render.config import load_config

source = Path(__file__).relative_to(Path.cwd()).parent / 'e2e/render/initial/petstore/lapidary/openapi/openapi.yaml'


def test_init_save_copies_document(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / 'output'
    from lapidary.render.cli import app

    result = runner.invoke(app, ('init', '--save', str(source), str(output), 'petstore'))
    if result.exception:
        raise result.exception
    assert result.exit_code == 0
    assert (output / 'lapidary/openapi/openapi.yaml').is_file()

    config = load_config(output)
    assert config.origin is None
    assert config.document_path == 'lapidary/openapi/openapi.yaml'


def test_init_doesnt_copy_document(tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / 'output'
    from lapidary.render.cli import app

    result = runner.invoke(app, ('init', str(source), str(output), 'petstore'))
    if result.exception:
        raise result.exception
    assert result.exit_code == 0
    assert not (output / 'lapidary/openapi/petstore.json').is_file()

    config = load_config(output)
    assert config.document_path == str(Path.cwd() / source)


def test_init_url_saves_origin(tmp_path: Path) -> None:
    from lapidary.render.cli import app

    runner = CliRunner()
    output = tmp_path / 'output'
    source = 'https://petstore3.swagger.io/api/v3/openapi.json'
    result = runner.invoke(app, ('init', str(source), str(output), 'petstore'))
    if result.exit_code != 0:
        print(result.output)
        print(result.exception)

    assert result.exit_code == 0

    config = load_config(output)
    assert str(config.origin) == source
    assert config.document_path == 'lapidary/openapi/openapi.json'
