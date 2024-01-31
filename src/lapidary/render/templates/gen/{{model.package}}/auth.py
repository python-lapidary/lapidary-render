# {% include 'includes/header.txt' %}
{% set model = auth_module -%}

import dataclasses
{%- for imp in model.imports %}
import {{ imp }}
{%- endfor %}

@dataclasses.dataclass
class Auth:
{%- for name, auth_model in model.schemes.items() %}
    {{ name }}: {{ lapidary.type_hint(auth_model, model.path) }}
{%- else %}
    pass
{%- endfor %}
