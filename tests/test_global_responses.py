import unittest

import yaml
from lapidary.render.model import openapi
from lapidary.render.model.client_module import get_client_class_module
from lapidary.render.model.openapi import OpenApiModel
from lapidary.render.model.python.module_path import ModulePath
from lapidary.render.model.python.type_hint import TypeHint
from lapidary.render.model.refs import get_resolver


class GlobalResponsesTest(unittest.TestCase):
    def test_ref_global_responses_in_output_model(self):
        with open('global_responses_ref.yaml') as doc_file:
            doc = yaml.safe_load(doc_file)
        model = OpenApiModel.model_validate(doc)

        module_path = ModulePath('test')
        module = get_client_class_module(model, module_path / 'client.py', module_path, get_resolver(model, 'test'))

        expected = {
            TypeHint(module='test.components.schemas', name='GSMTasksError'),
        }

        self.assertEqual(expected, module.body.init_method.response_types)

    def test_inline_global_responses_in_output_model(self):
        with open('global_responses_inline.yaml') as doc_file:
            doc = yaml.safe_load(doc_file)
        model = openapi.OpenApiModel.model_validate(doc)

        module_path = ModulePath('test')
        module = get_client_class_module(model, module_path / 'client.py', module_path, get_resolver(model, 'test'))

        expected = {
            TypeHint(module='test.components.schemas', name='GSMTasksError'),
        }

        self.assertEqual(expected, module.body.init_method.response_types)
