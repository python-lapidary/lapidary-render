from __future__ import annotations

__all__ = [
    'APIKeySecurityScheme',
    'AuthorizationCodeOAuthFlow',
    'Callback',
    'ClientCredentialsFlow',
    'Components',
    'Contact',
    'Discriminator',
    'Encoding',
    'Example',
    'ExternalDocumentation',
    'HTTPSecurityScheme',
    'Header',
    'ImplicitOAuthFlow',
    'In',
    'In1',
    'In2',
    'In3',
    'In4',
    'Info',
    'License',
    'Link',
    'MediaType',
    'OAuth2SecurityScheme',
    'OAuthFlows',
    'OpenApiModel',
    'OpenIdConnectSecurityScheme',
    'Operation',
    'Parameter',
    'ParameterLocation',
    'ParameterLocationItem',
    'ParameterLocationItem1',
    'ParameterLocationItem2',
    'ParameterLocationItem3',
    'PasswordOAuthFlow',
    'PathItem',
    'Paths',
    'Reference',
    'RequestBody',
    'Required',
    'Response',
    'Responses',
    'Schema',
    'SecurityRequirement',
    'SecurityScheme',
    'Server',
    'ServerVariable',
    'Style',
    'Style1',
    'Style2',
    'Style4',
    'Tag',
    'Type',
    'Type1',
    'Type2',
    'Type3',
    'Type4',
    'XML'
]


import typing

from typing_extensions import TypeAlias

from .ext import *
from .model import *
from .utils import get_operations

SchemaOrRef: TypeAlias = typing.Union[Schema, Reference]
