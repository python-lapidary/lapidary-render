# This file is automatically @generated by Lapidary and should not be changed by hand.

from __future__ import annotations

import typing

import lapidary.runtime
import pydantic
import typing_extensions
import lapidary.runtime


class Tag(lapidary.runtime.ModelBase):
    id: typing.Annotated[
        typing.Union[None, int],
        pydantic.Field(
        )
    ] = None

    name: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
        )
    ] = None

    model_config = pydantic.ConfigDict(
        extra='allow'
    )
