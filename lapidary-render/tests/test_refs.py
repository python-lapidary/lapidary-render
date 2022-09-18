from unittest import TestCase

from lapis.openapi import model as openapi
from lapis.render.elems.refs import resolve
from lapis.render.module_path import ModulePath
from lapis.render.type_ref import get_type_ref, TypeRef

schema_carol = openapi.Schema()
schema_bob = openapi.Schema(properties={'carol': schema_carol})
model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='', version=''),
    paths=openapi.Paths(__root__={}),
    components=openapi.Components(
        schemas={
            'alice': openapi.Reference(**{'$ref': '#/components/schemas/bob'}),
            'bob': schema_bob,

            'joker': openapi.Reference(**{'$ref': '#/components/schemas/joker'}),

            'batman': openapi.Reference(**{'$ref': '#/components/schemas/robin'}),
            'robin': openapi.Reference(**{'$ref': '#/components/schemas/batman'}),

            'charlie': openapi.Schema(oneOf=[
                openapi.Schema()
            ]),
        }
    )
)


class ReferenceTest(TestCase):
    def test_resolve_ref(self):
        self.assertEqual(
            resolve(model, 'root', openapi.Reference(**{'$ref': '#/components/schemas/alice'}), openapi.Schema),
            (schema_bob, ModulePath('root.components.schemas.bob'), 'bob')
        )

    def test_nested_schema(self):
        self.assertEqual(
            resolve(model, 'root', openapi.Reference(**{'$ref': '#/components/schemas/bob/properties/carol'}), openapi.Schema),
            (schema_carol, ModulePath('root.components.schemas.bob.properties.carol'), 'carol')
        )

    def test_direct_recursion_fails(self):
        def raises():
            resolve(model, 'root', openapi.Reference(**{'$ref': '#/components/schemas/joker'}), openapi.Schema)

        self.assertRaises(RecursionError, raises)

    def test_indirect_recursion_fails(self):
        def raises():
            resolve(model, 'root', openapi.Reference(**{'$ref': '#/components/schemas/batman'}), openapi.Schema)

        self.assertRaises(RecursionError, raises)

    def test_empty_schema_generate_any_type_ref(self):
        type_ref = get_type_ref(openapi.Schema(), ModulePath('lapis_test'), 'empty_schema', True, None)
        self.assertEqual(type_ref, TypeRef.from_str('typing.Any'))
