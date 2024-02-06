from dataclasses import dataclass, field
from typing import Mapping, Optional

import pydantic

from .module import AbstractModule
from .param import ParamLocation
from .type_hint import TypeHint


class AuthModel(pydantic.BaseModel):
    pass


class ApiKeyAuthModel(AuthModel):
    param_name: str
    placement: ParamLocation


class HttpAuthModel(AuthModel):
    scheme: str
    bearer_format: Optional[str]


@dataclass(frozen=True, kw_only=True)
class AuthModule(AbstractModule):
    schemes: Mapping[str, TypeHint] = field()
    model_type = 'auth'
