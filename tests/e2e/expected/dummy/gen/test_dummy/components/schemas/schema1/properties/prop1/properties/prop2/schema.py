# This file is automatically @generated by Lapidary and should not be changed by hand.

from __future__ import annotations

import lapidary.runtime
import pydantic
import typing_extensions as typing


class prop2(lapidary.runtime.ModelBase):
    key: typing.Annotated[
        str,
        pydantic.Field(
            max_length=10,
            min_length=5,
        )
    ]

    nonu_lalpha: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
            alias='non/alpha',
        )
    ]