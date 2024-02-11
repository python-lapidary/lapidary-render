from dataclasses import dataclass

from .attribute import AttributeModel
from .type_hint import TypeHint


@dataclass(frozen=True)
class OperationFunctionModel:
    name: str
    request_type: TypeHint | None
    params: list[AttributeModel]
    response_type: TypeHint | None
    auth_name: str | None
    docstr: str | None = None
