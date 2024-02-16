import dataclasses as dc
from typing import Annotated, Any

from typing_extensions import Doc

from lapidary.runtime.model.params import ParamLocation

from . import AttributeModel


@dc.dataclass(kw_only=True)
class Parameter(AttributeModel):
    in_: ParamLocation
    default: Annotated[Any, Doc('Default value, used only for global headers.')] = None
    media_type: str | None = None
