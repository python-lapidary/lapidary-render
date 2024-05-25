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
            alias='id',
        )
    ] = None

    petId: typing.Annotated[
        typing.Union[None, int],
        pydantic.Field(
            alias='petId',
        )
    ] = None

    quantity: typing.Annotated[
        typing.Union[None, int],
        pydantic.Field(
            alias='quantity',
        )
    ] = None

    shipDate: typing.Annotated[
        typing.Union[None, datetime.datetime],
        pydantic.Field(
            alias='shipDate',
        )
    ] = None

    status: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
            alias='status',
        )
    ] = None

    complete: typing.Annotated[
        typing.Union[None, bool],
        pydantic.Field(
            alias='complete',
        )
    ] = None

    model_config = pydantic.ConfigDict(
        extra='allow'
    )
