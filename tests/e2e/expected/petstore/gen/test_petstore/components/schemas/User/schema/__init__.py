# This file is automatically @generated by Lapidary and should not be changed by hand.

from __future__ import annotations

import typing

import lapidary.runtime
import pydantic
import typing_extensions
import lapidary.runtime


class User(lapidary.runtime.ModelBase):
    id_: typing.Annotated[
        typing.Union[None, int],
        pydantic.Field(
            alias='id',
        )
    ] = None

    username: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
            alias='username',
        )
    ] = None

    firstName: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
            alias='firstName',
        )
    ] = None

    lastName: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
            alias='lastName',
        )
    ] = None

    email: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
            alias='email',
        )
    ] = None

    password: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
            alias='password',
        )
    ] = None

    phone: typing.Annotated[
        typing.Union[None, str],
        pydantic.Field(
            alias='phone',
        )
    ] = None

    userStatus: typing.Annotated[
        typing.Union[None, int],
        pydantic.Field(
            alias='userStatus',
        )
    ] = None

    model_config = pydantic.ConfigDict(
        extra='allow'
    )
