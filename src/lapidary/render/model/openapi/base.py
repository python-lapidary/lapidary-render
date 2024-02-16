import re
import typing

import pydantic

from ...pydantic_utils import find_annotation_optional


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        populate_by_name=True,
        extra='allow',
        frozen=True,
    )


class ExtendableModel(BaseModel):
    """Base model class for model classes that accept extension fields, i.e. with keys start with 'x-'"""

    model_config = pydantic.ConfigDict(
        # Allow extra properties, but don't keep them.
        extra='ignore',
    )


class PropertyPattern:
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern


class ModelWithAdditionalProperties(BaseModel):
    model_config = pydantic.ConfigDict(
        extra='allow',
    )


class ModelWithPatternProperties(BaseModel):
    @pydantic.model_validator(mode='before')
    @classmethod
    def validate(cls, value: typing.Any, info: pydantic.ValidationInfo):
        for field_name, field_info in cls.model_fields.items():
            pattern_anno = find_annotation_optional(field_info.metadata, PropertyPattern)
            if not pattern_anno:
                continue

            pattern = re.compile(pattern_anno.pattern)

            pattern_props = {}
            for key, item in value.items():
                if pattern.search(key):
                    pattern_props[key] = item
            for key in pattern_props:
                del value[key]
            value[field_name] = pattern_props

        return value
