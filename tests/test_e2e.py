import shutil
from collections.abc import Iterator
from pathlib import Path

import anyio
import pytest
import ruamel.yaml

from lapidary.render.main import render_project


@pytest.fixture()
def yaml():
    return ruamel.yaml.YAML(typ='safe')


e2e_root = Path(__file__).parent / 'e2e'
e2e_tests = [path.name for path in (e2e_root / 'init').iterdir() if path.is_dir()]


@pytest.mark.parametrize(
    'project_name',
    e2e_tests,
    ids=e2e_tests,
)
@pytest.mark.asyncio
async def test_generate(yaml: ruamel.yaml.YAML, project_name: Path, tmp_path: Path) -> None:
    init_root = e2e_root / 'init' / project_name
    project_root = tmp_path / 'project'

    shutil.copytree(init_root, project_root)
    assert project_root.is_dir()

    await render_project(anyio.Path(project_root))

    expected = e2e_root / 'expected' / project_name

    assert set(dir_contents_stream(project_root)) == set(dir_contents_stream(expected))


def dir_contents_stream(root: Path) -> Iterator[tuple[Path, str]]:
    for path in root.rglob('*'):
        if not path.is_dir():
            try:
                yield path.relative_to(root), path.read_text()
            except UnicodeDecodeError as e:
                e.add_note(str(path))
                raise
