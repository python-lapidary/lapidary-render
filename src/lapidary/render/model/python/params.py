import enum

from .module_path import ModulePath
from .names import PARAM_MODEL
from .type_hint import TypeHint, get_type_hint
from .. import openapi
from ..refs import ResolverFunc


class ParamDirection(enum.Flag):
    """Use read for readOnly, write for writeOnly; read+write if unset"""

    read = enum.auto()
    write = enum.auto()


class ParamLocation(enum.Enum):
    cookie = 'cookie'
    header = 'header'
    path = 'path'
    query = 'query'


def get_param_type(
        param: openapi.Parameter, module_: ModulePath, resolve: ResolverFunc
) -> TypeHint:
    if isinstance(param.schema_, openapi.Reference):
        schema, module, schema_name = resolve(param.schema_, openapi.Schema)
    else:
        schema = param.schema_
        param_name = param.effective_name
        schema_name = param_name
        module = module_ / PARAM_MODEL

    return get_type_hint(schema, module, schema_name, param.required, resolve)
