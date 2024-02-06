from ..names import PARAM_MODEL
from . import openapi, python
from .refs import ResolverFunc
from .type_hint import get_type_hint


def get_param_type(
        param: openapi.Parameter, module_: python.ModulePath, resolve: ResolverFunc
) -> python.TypeHint:
    if isinstance(param.schema_, openapi.Reference):
        schema, module, schema_name = resolve(param.schema_, openapi.Schema)
    else:
        schema = param.schema_
        param_name = param.effective_name
        schema_name = param_name
        module = module_ / PARAM_MODEL

    return get_type_hint(schema, module, schema_name, param.required, resolve)
