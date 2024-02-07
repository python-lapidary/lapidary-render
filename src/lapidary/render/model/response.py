import pkgutil

from ..names import RESPONSE_BODY, response_type_name
from . import openapi, python
from .refs import ResolverFunc, get_resolver
from .type_hint import get_type_hint


def get_response_map(
    responses: openapi.Responses, op_name: str, module: python.ModulePath, resolve_ref: ResolverFunc
) -> python.ResponseMap:
    result = {}
    for resp_code, response in responses.responses.items():
        response, sub_module, sub_name = resolve_response(resp_code, response, op_name, module, resolve_ref)
        if not response.content:
            continue

        mime_map = {}
        for mime, media_type in response.content.items():
            if isinstance(media_type.schema_, openapi.Reference):
                resp_schema, resp_module, resp_name = resolve_ref(media_type.schema_, openapi.Schema)
            else:
                resp_schema = media_type.schema_
                resp_module = sub_module
                resp_name = sub_name
            mime_map[mime] = get_type_hint(resp_schema, resp_module, resp_name, True, resolve_ref)

        result[resp_code] = mime_map

    return result


def resolve_response(
    resp_code: str,
    response: openapi.Response | openapi.Reference,
    op_name: str,
    module: python.ModulePath,
    resolve_ref: ResolverFunc,
) -> tuple[openapi.Response, python.ModulePath, str]:
    if isinstance(response, openapi.Reference):
        response, sub_module, sub_name = resolve_ref(response, openapi.Response)
    else:
        sub_module = module / RESPONSE_BODY
        response_type_name(op_name, resp_code)
        sub_name = response_type_name(op_name, resp_code)
    return response, sub_module, sub_name


def get_api_responses(model: openapi.OpenApiModel, module: python.ModulePath) -> python.ResponseMap:
    resolve_ref = get_resolver(model, str(module))
    return get_response_map(model.lapidary_responses_global, 'API', module, resolve_ref)


def resolve_type(
    schema: openapi.Schema | openapi.Reference,
    module: python.ModulePath,
    resolve_ref: ResolverFunc,
) -> type:
    if isinstance(schema, openapi.Reference):
        _, module, name = resolve_ref(schema, openapi.Schema)
    elif schema.lapidary_name is not None:
        name = schema.lapidary_name
    else:
        raise NotImplementedError('Schema needs name')
    return pkgutil.resolve_name(str(module) + ':' + name)
