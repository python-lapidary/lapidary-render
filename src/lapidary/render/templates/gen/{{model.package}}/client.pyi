# {% include 'includes/header.txt' %}

__all__ = [
    'ApiClient',
    'Auth',
]

import typing

import lapidary.runtime
import lapidary.runtime.auth
import pydantic

import {{ model.package }}.auth
from {{ model.package }}.auth import Auth

{%- for imp in model.imports %}
import {{ imp }}
{%- endfor %}

class ApiClient(lapidary.runtime.ClientBase):
    def __init__(
        self,
        *,
        auth: {{ model.package }}.auth.Auth,
        base_url=
{%- if model.base_urls | length > 0 -%}
        '{{ model.base_urls[0] }}',
{%- else -%}
        None,
{%- endif %}
    ):
        ...

{% for func in model.client.body.methods | sort(attribute='name') %}
{%- include 'includes/client/method_operation.py' %}
{%- else %}
    pass
{%- endfor %}
