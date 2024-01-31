from collections.abc import Mapping, Collection
from dataclasses import dataclass, field
from typing import Optional, Union

from .auth import AuthModel, get_auth_models
from .response_map import get_api_responses, ResponseMap
from ..module_path import ModulePath
from ..openapi import model as openapi


@dataclass(frozen=True)
class ClientInit:
    default_auth: Optional[str]
    auth_models: Mapping[str, AuthModel] = field(default_factory=dict)
    base_url: Optional[str] = None
    headers: list[tuple[str, str]] = field(default_factory=list)
    response_map: Optional[ResponseMap] = field(default_factory=dict)


def get_client_init(openapi_model: openapi.OpenApiModel, module: ModulePath) -> ClientInit:
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

    return ClientInit(
        base_url=base_url,
        headers=get_global_headers(openapi_model.lapidary_headers_global),
        default_auth=default_auth,
        response_map=api_responses,
        auth_models=auth_models,
    )


def get_global_headers(global_headers: Optional[Union[
    dict[str, Union[str, list[str]]],
    list[tuple[str, str]]
]]) -> list[tuple[str, str]]:
    """Normalize headers structure"""
    if global_headers is None:
        return []

    result_headers = []
    input_header_list = global_headers.items() if isinstance(global_headers, Mapping) else global_headers
    for key, values in input_header_list:
        if not isinstance(values, Collection) or isinstance(values, str):
            values = [values]
        for value in values:
            result_headers.append((key, value,))

    return result_headers
