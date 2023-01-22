{%- import 'includes/type_hint.py.jinja' as th %}
{%- macro render_param(param) %}
        {{ param.name }}: {{ th.type_hint(param.annotation.type, path) }}{% if not param.required %} = lapidary.runtime.absent.ABSENT{% endif %},
{%- endmacro %}
    async def {{ func.name }}(
        self,
{%- if func.request_type is not none %}
        request_body: {{ th.type_hint(func.request_type, path) }}, /, {% endif %}
{%- if func.params | length > 0 %}
        *,{% endif %}
{%- for param in func.params if param.required %}
        {{- render_param(param) }}
{%- endfor %}{% for param in func.params if not param.required %}
        {{- render_param(param) }}
{%- endfor %}
    ) -> {{ th.type_hint(func.response_type, path) }}:
        ...
