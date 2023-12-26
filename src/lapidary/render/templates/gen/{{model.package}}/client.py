# {% include 'includes/header.txt' %}

__all__ = [
    'ApiClient',
    'Auth',
]

import lapidary.runtime
from {{ model.package }}.auth import Auth


class ApiClient(lapidary.runtime.ClientBase):
    pass
