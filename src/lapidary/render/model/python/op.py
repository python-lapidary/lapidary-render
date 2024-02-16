from collections.abc import Iterable
from typing import NamedTuple

from .attribute import AttributeModel
from .type_hint import TypeHint


class OperationFunctionModel(NamedTuple):
    name: str
    request_type: TypeHint | None
    params: Iterable[AttributeModel] = ()
    response_type: TypeHint | None = None
    auth_name: str | None = None
    docstr: str | None = None
