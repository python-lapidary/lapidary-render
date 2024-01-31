from dataclasses import dataclass, field
from typing import Mapping, Optional

from . import openapi
from lapidary.render.model.python.type_hint import TypeHint
from lapidary.render.model.python.module_path import ModulePath

from .module import AbstractModule


@dataclass(frozen=True, kw_only=True)
class AuthModule(AbstractModule):
    schemes: Mapping[str, TypeHint] = field()
    model_type = 'auth'


def get_auth_module(openapi_model: openapi.OpenApiModel, module: ModulePath) -> Optional[AuthModule]:
    schemes = {
        name: get_auth_param_type(value) for name, value in openapi_model.components.securitySchemes.items()
    } if openapi_model.components and openapi_model.components.securitySchemes else {}
    imports = list({
        import_
        for scheme in schemes.values()
        for import_ in scheme.imports()
    })
    return AuthModule(
        schemes=schemes,
        imports=imports,
        path=module,
    )


def get_auth_param_type(security_scheme: openapi.SecurityScheme) -> TypeHint:
    scheme = security_scheme.__root__
    if isinstance(scheme, openapi.APIKeySecurityScheme):
        return TypeHint.from_str('lapidary.runtime.auth:APIKey')
    elif isinstance(scheme, openapi.HTTPSecurityScheme):
        return TypeHint.from_str('lapidary.runtime.auth:HTTP')
    elif isinstance(scheme, openapi.OAuth2SecurityScheme):
        if scheme.flows.password:
            return TypeHint.from_str('lapidary.runtime.auth:OAuth2')
        raise NotImplementedError(type(scheme).__name__)
    else:
        raise NotImplementedError(scheme.__name__)
