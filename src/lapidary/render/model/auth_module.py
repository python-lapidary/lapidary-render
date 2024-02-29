import typing
from functools import singledispatch

from . import openapi, python


def get_auth_module(openapi_model: openapi.OpenApiModel, module: python.ModulePath) -> python.AuthModule | None:
    schemes = (
        {name: get_auth_param_type(value) for name, value in openapi_model.components.securitySchemes.items()}
        if openapi_model.components and openapi_model.components.securitySchemes
        else {}
    )
    return python.AuthModule(
        schemes=schemes,
        path=module,
    )


def get_auth_param_type(security_scheme: openapi.SecurityScheme) -> python.type_hint.TypeHint:
    scheme = security_scheme.__root__
    if isinstance(scheme, openapi.APIKeySecurityScheme):
        return python.type_hint.TypeHint.from_str('lapidary.runtime.auth:APIKey')
    elif isinstance(scheme, openapi.HTTPSecurityScheme):
        return python.type_hint.TypeHint.from_str('lapidary.runtime.auth:HTTP')
    elif isinstance(scheme, openapi.OAuth2SecurityScheme):
        if scheme.flows.password:
            return python.type_hint.TypeHint.from_str('lapidary.runtime.auth:OAuth2')
        raise NotImplementedError(type(scheme).__name__)
    else:
        raise NotImplementedError(scheme.__name__)


def get_auth_models(
    model: dict[str, openapi.Reference | openapi.SecurityScheme],
) -> typing.Mapping[str, python.Auth]:
    result: typing.Mapping[str, python.Auth] = {name: get_auth_model(scheme) for name, scheme in model.items()}
    return result


@singledispatch
def get_auth_model(scheme: typing.Any) -> python.Auth | None:
    raise NotImplementedError(scheme)


@get_auth_model.register(openapi.SecurityScheme)
def _(scheme: openapi.SecurityScheme):
    return get_auth_model(scheme.__root__)


@get_auth_model.register(openapi.APIKeySecurityScheme)
def _(scheme: openapi.APIKeySecurityScheme):
    return python.ApiKeyAuth(
        placement=python.ParamLocation[scheme.in_.value],
        param_name=scheme.name,
    )


@get_auth_model.register(openapi.HTTPSecurityScheme)
def _(scheme: openapi.HTTPSecurityScheme):
    return python.HttpAuth(
        scheme=scheme.scheme,
        bearer_format=scheme.bearerFormat,
    )
