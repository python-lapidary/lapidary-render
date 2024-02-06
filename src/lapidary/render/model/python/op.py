from dataclasses import dataclass
from typing import Optional, Type

from .attribute import AttributeModel
from .response import ResponseMap
from .type_hint import TypeHint


@dataclass(frozen=True)
class OperationModel:
    method: str
    path: str
    params_model: Optional[Type]
    response_map: Optional[ResponseMap]


@dataclass(frozen=True)
class OperationFunctionModel:
    name: str
    request_type: Optional[TypeHint]
    params: list[AttributeModel]
    response_type: Optional[TypeHint]
    auth_name: Optional[str]
    docstr: Optional[str] = None
