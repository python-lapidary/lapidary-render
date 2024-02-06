import typing

from . import openapi, python
from .auth_module import get_auth_models
from .response import get_api_responses


def get_client_init(openapi_model: openapi.OpenApiModel, module: python.ModulePath) -> python.ClientInit:
    default_auth = next(iter(openapi_model.security[0].__root__.keys())) if openapi_model.security else None

    base_url = (
        openapi_model.servers[0].url if openapi_model.servers and openapi_model.servers
        else None
    )

    auth_models = (
        get_auth_models(openapi_model.components.securitySchemes)
        if openapi_model.components and openapi_model.components.securitySchemes
        else {}
    )

    api_responses = get_api_responses(openapi_model, module) if openapi_model.lapidary_responses_global else {}

    return python.ClientInit(
        base_url=base_url,
        headers=get_global_headers(openapi_model.lapidary_headers_global),
        default_auth=default_auth,
        response_map=api_responses,
        auth_models=auth_models,
    )


def get_global_headers(global_headers: dict[str, str | list[str]] | list[tuple[str, str]] | None) -> list[tuple[str, str]]:
    """Normalize headers structure"""
    if global_headers is None:
        return []

    result_headers = []
    input_header_list = global_headers.items() if isinstance(global_headers, typing.Mapping) else global_headers
    for key, values in input_header_list:
        if not isinstance(values, typing.Collection) or isinstance(values, str):
            values = [values]
        for value in values:
            result_headers.append((key, value,))

    return result_headers
