# This file is automatically @generated by Lapidary and should not be changed by hand.

from __future__ import annotations

from lapidary.runtime import *
import pydantic
import typing_extensions as typing
import datetime


class ResponseMetadata(pydantic.BaseModel):
    Xu_jRateu_jLimit: typing.Annotated[typing.Union[None, int], Header('X-Rate-Limit', style=SimpleMultimap,)] = None
    Xu_jExpiresu_jAfter: typing.Annotated[typing.Union[None, datetime.datetime], Header('X-Expires-After', style=SimpleMultimap,)] = None
