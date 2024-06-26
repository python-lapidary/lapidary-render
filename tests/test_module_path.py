from lapidary.render.model.python import ModulePath


def test_relative_to():
    parent = ModulePath('a.b')
    child = ModulePath('a.b.c')
    assert child @ parent == ModulePath('c')
