from lapidary.render.model import python, schema, stack


def test_resolve_type_hint():
    expected = python.TypeHint(module='pkg.paths.u_lpathu_l.get.parameters.u_m', name='schema')
    type_hint = schema.resolve_type_hint('pkg', stack.Stack.from_str('#/paths/~1path~1/get/parameters/0/schema'))
    assert type_hint == expected
