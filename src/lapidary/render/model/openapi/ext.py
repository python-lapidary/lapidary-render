import enum

__all__ = [
    'LapidaryModelType',
]


class LapidaryModelType(enum.Enum):
    model = 'model'
    """The default type, rendered as a subclass of pydantic.BaseModel."""

    exception = 'exception'
    """Error typy, not used as return type, if received, it's raised."""
