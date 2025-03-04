import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from lapidary.render.main import render_project

e2e_root = Path(__file__).parent / 'e2e'
e2e_tests = [path.name for path in (e2e_root / 'init').iterdir() if path.is_dir()]


@pytest.mark.parametrize(
    'project_name',
    e2e_tests,
    ids=e2e_tests,
)
def test_generate(project_name: Path, tmp_path: Path) -> None:
    init_root = e2e_root / 'init' / project_name
    project_root = tmp_path / 'project'

    shutil.copytree(init_root, project_root)
    assert project_root.is_dir()

    render_project(project_root)

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
