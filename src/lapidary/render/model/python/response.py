import typing
from collections.abc import Mapping

T = typing.TypeVar('T')
MimeType = ResponseCode = str


class ReturnTypeInfo(typing.NamedTuple):
    type_: type


MimeMap = Mapping[MimeType, ReturnTypeInfo]
ResponseMap = Mapping[ResponseCode, MimeMap]
