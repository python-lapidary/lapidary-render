# This file is automatically @generated by Lapidary and should not be changed by hand.

from __future__ import annotations

import typing

import lapidary.runtime
import pydantic
import typing_extensions
import lapidary.runtime


class prop2(lapidary.runtime.ModelBase):
    key: typing.Annotated[
        str,
        pydantic.Field(
            alias='key',
            max_length=10,
            min_length=5,
        )
    ]
