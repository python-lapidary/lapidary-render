# This file is automatically @generated by Lapidary and should not be changed by hand.

from __future__ import annotations

import typing_extensions as typing
from lapidary.runtime import *
import test_petstore.components.schemas.User.schema


class Response(ResponseEnvelope):
    body: typing.Annotated[test_petstore.components.schemas.User.schema.User, ResponseBody()]
