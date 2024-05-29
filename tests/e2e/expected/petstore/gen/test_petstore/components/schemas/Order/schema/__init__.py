# This file is automatically @generated by Lapidary and should not be changed by hand.

from __future__ import annotations

import typing

import lapidary.runtime
import pydantic
import typing_extensions
import datetime
import lapidary.runtime


class Order(lapidary.runtime.ModelBase):
    id: typing.Annotated[
        typing.Union[None, int],
        pydantic.Field(
        )
    ] = None

    petId: typing.Annotated[
        typing.Union[None, int],
        pydantic.Field(
        )
    ] = None

    quantity: typing.Annotated[
        typing.Union[None, int],
        pydantic.Field(
        )
    ] = None

    shipDate: typing.Annotated[
        typing.Union[None, datetime.datetime],
        pydantic.Field(
        )
    ] = None

    status: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
        )
    ] = None

    complete: typing.Annotated[
        typing.Union[None, bool],
        pydantic.Field(
        )
    ] = None

    model_config = pydantic.ConfigDict(
        extra='allow'
    )
