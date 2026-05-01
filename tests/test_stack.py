from lapidary_render.model import conv_schema, python, stack
from lapidary_render.model.python import AnnotatedType


def test_resolve_type_hint():
    expected = AnnotatedType(python.NameRef('pkg.paths.u_lpathu_l.get.parameters.u_m', 'schema'))
    type_hint = conv_schema.resolve_type_name('pkg', stack.Stack.from_str('#/paths/~1path~1/get/parameters/0/schema'))
    assert type_hint == expected
