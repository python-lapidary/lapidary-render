# This file is automatically @generated by Lapidary and should not be changed by hand.

from __future__ import annotations

import typing

import lapidary.runtime
import pydantic
import typing_extensions
import lapidary.runtime
import test_dummy.components.schemas.all.properties.any.schema
import test_dummy.components.schemas.all.properties.u_000000for.schema


class all(lapidary.runtime.ModelBase):
    u_000000for: typing.Annotated[
        test_dummy.components.schemas.all.properties.u_000000for.schema.u_000000for,
        pydantic.Field(
            alias='for',
        )
    ]

    any: typing.Annotated[
        typing.Union[None, test_dummy.components.schemas.all.properties.any.schema.any],
        pydantic.Field(
            alias='any',
        )
    ] = None

    uu_00005f000000for: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
            alias='u_000000for',
        )
    ] = None
