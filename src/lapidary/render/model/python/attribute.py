from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .type_hint import TypeHint


@dataclass(frozen=True)
class AttributeModel:
    name: str
    annotation: AttributeAnnotationModel
    deprecated: bool = False
    """Currently not used"""

    required: Optional[bool] = None
    """
    Used for op method params. Required params are rendered before optional, and optional have default value ABSENT
    """


@dataclass(frozen=True)
class AttributeAnnotationModel:
    type: TypeHint
    field_props: dict[str, Any]

    default: Optional[str] = None
    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = False
