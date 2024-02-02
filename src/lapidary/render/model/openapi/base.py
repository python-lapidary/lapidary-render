from abc import abstractmethod
from collections.abc import ItemsView
from typing import Any, Generic, Mapping, TypeVar

import pydantic


class ExtendableModel(pydantic.BaseModel):
    """Base model class for model classes that accept extension fields, i.e. with keys start with 'x-'"""

    class Config(pydantic.BaseConfig):
        extra = pydantic.Extra.allow

    @pydantic.model_validator(mode='before')
    @classmethod
    def validate_extras(cls, values: Mapping[str, Any]) -> Mapping[str, Any]:
        if not values or not isinstance(values, Mapping):
            return values
        aliases = (info.alias for info in cls.model_fields.values() if info.alias)

        for key, value in values.items():
            key: str
            if not (
                    key in cls.model_fields
                    or key in aliases
                    or key.startswith('x-')
            ):
                raise ValueError(f'{key} field not permitted')
        return values

    def __getitem__(self, item: str) -> Any:
        if not item.startswith('x-'):
            raise KeyError(item)
        return self.__dict__[item]


T = TypeVar('T')


class DynamicExtendableModel(Generic[T], pydantic.BaseModel):
    """
    Base model class for classes with patterned fields of type T, ond extension fields (x-) of any type.
    This is equivalent of pydantic custom root type, where __root__: dict[str, T] but for keys starting with 'x-',
    it's __root__: dict[str, Any].

    Instances support accessing fields by index (e.g. paths['/']), which can return any existing attribute,
    as well as items() wich returns ItemsView with only pattern attributes.
    """

    model_config = pydantic.ConfigDict(
        extra='allow',
    )

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_model(cls, values: Mapping[str, Any]):
        for key, value in values.items():
            if not key.startswith('x-'):
                if not cls._validate_key(key):
                    raise ValueError(f'{key} field not permitted')

        return values

    @classmethod
    @abstractmethod
    def _validate_key(cls, key: str) -> bool:
        pass

    def __getitem__(self, item: str) -> Any:
        return self.__dict__[item]

    def items(self) -> ItemsView[str, T]:
        """:returns: ItemsView (just like dict.items()) that excludes extension fields (those with keys starting with 'x-')"""
        return {key: value for key, value in self.__dict__.items() if not key.startswith('x-')}.items()

    def __contains__(self, item: str) -> bool:
        return item in self.__dict__

    def get(self, key: str, default_value: Any) -> Any:
        return self.__dict__.get(key, default_value)
