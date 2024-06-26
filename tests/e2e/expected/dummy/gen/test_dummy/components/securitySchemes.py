# This file is automatically @generated by Lapidary and should not be changed by hand.


from collections.abc import Iterable
from typing import Union

import httpx
import httpx_auth
import lapidary.runtime.auth
from lapidary.runtime import NamedAuth
from typing_extensions import Literal


def oauth2_implicit_oauth(
    scope: Union[Iterable[Literal['read', 'write']], None] = None,
    **kwargs,
) -> NamedAuth:
    if scope is not None:
        kwargs['scope'] = ' '.join(scope)

    return 'oauth', httpx_auth.OAuth2Implicit(
        authorization_url='https://example.com/authorization_url',
        **kwargs,
    )


def oauth2_password_oauth(
    username: str,
    password: str,
    scope: Union[Iterable[Literal['read', 'write']], None] = None,
    **kwargs,
) -> NamedAuth:
    if scope is not None:
        kwargs['scope'] = ' '.join(scope)

    return 'oauth', httpx_auth.OAuth2ResourceOwnerPasswordCredentials(
        token_url='https://example.com/token_url',
        username=username,
        password=password,
        **kwargs,
    )


def oauth2_authorization_code_oauth(
    scope: Union[Iterable[Literal['read', 'write']], None] = None,
    **kwargs,
) -> NamedAuth:
    if scope is not None:
        kwargs['scope'] = ' '.join(scope)

    return 'oauth', httpx_auth.OAuth2AuthorizationCode(
        authorizaiton_url='https://example.com/authorization_url',
        token_url='https://example.com/token_url',
        **kwargs,
    )


def oauth2_client_credentials_oauth(
    client_id: str,
    client_secret: str,
    scope: Union[Iterable[Literal['read', 'write']], None] = None,
    **kwargs,
) -> NamedAuth:
    if scope is not None:
        kwargs['scope'] = ' '.join(scope)

    return 'oauth', httpx_auth.OAuth2ClientCredentials(
        token_url='https://example.com/token_url',
        client_id=client_id,
        client_secret=client_secret,
        **kwargs,
    )


def api_key_apiu_jkey(api_key: str) -> NamedAuth:
    return 'api-key', lapidary.runtime.auth.HeaderApiKey(
        api_key=api_key,
        header_name='x-api-key',
    )


def api_key_apiu_jkeyu_jcookie(api_key: str) -> NamedAuth:
    return 'api-key-cookie', lapidary.runtime.auth.CookieApiKey(
        api_key=api_key,
        cookie_name='x-api-key',
    )


def api_key_apiu_jkeyu_jquery(api_key: str) -> NamedAuth:
    return 'api-key-query', lapidary.runtime.auth.QueryApiKey(
        api_key=api_key,
        query_parameter_name='x-api-key',
    )


def http_basic_http_basic(user_name: str, password: str) -> NamedAuth:
    return 'http_basic', httpx.BasicAuth(
        username=user_name,
        password=password,
    )


def http_digest_http_digest(user_name: str, password: str) -> NamedAuth:
    return 'http_digest', httpx.DigestAuth(
        username=user_name,
        password=password,
    )
