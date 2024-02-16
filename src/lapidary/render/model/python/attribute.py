from __future__ import annotations

import dataclasses as dc
import typing

from .type_hint import TypeHint


@dc.dataclass
class AttributeModel:
    name: str
    annotation: AttributeAnnotationModel
    deprecated: bool = False
    """Currently not used"""

    required: bool | None = None
    """
    Used for op method params. Required params are rendered before optional, and optional have default value ABSENT
    """


@dc.dataclass(frozen=True)
class AttributeAnnotationModel:
    type: TypeHint
    field_props: dict[str, typing.Any]

    default: str | None = None
    style: str | None = None
    explode: bool | None = None
    allowReserved: bool | None = False
