import typing
from collections.abc import Mapping

from .type_hint import TypeHint

T = typing.TypeVar('T')
MimeType = ResponseCode = str

MimeMap = Mapping[MimeType, TypeHint]
ResponseMap = Mapping[ResponseCode, MimeMap]
