from dataclasses import dataclass

from .attribute import AttributeModel
from .response import ResponseMap
from .type_hint import TypeHint


@dataclass(frozen=True)
class OperationModel:
    method: str
    path: str
    params_model: type | None
    response_map: ResponseMap | None


@dataclass(frozen=True)
class OperationFunctionModel:
    name: str
    request_type: TypeHint | None
    params: list[AttributeModel]
    response_type: TypeHint | None
    auth_name: str | None
    docstr: str | None = None
