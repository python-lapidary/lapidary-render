{% include 'includes/header.py.jinja' %}
from __future__ import annotations

import typing

import lapidary.runtime
import pydantic
import typing_extensions

{%- for imp in item.imports %}
import {{ imp }}
{%- endfor %}
{% set path = item.path %}
{%- for model in item.body %}
{% include 'includes/schema/schema_class_' + model.model_type.name + '.py.jinja' %}
{%- endfor %}
{% for model in item.body %}{% if model.base_type.full_name() == 'pydantic.BaseModel' %}
{{ model.class_name }}.update_forward_refs()
{%- endif %}{% endfor %}
