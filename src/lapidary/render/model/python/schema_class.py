import dataclasses as dc
import enum
from collections.abc import Iterable

from .attribute import AttributeModel
from .module import AbstractModule
from .type_hint import TypeHint


class ModelType(enum.Enum):
    model = 'python'
    param_model = 'param_model'
    exception = 'exception'
    enum = 'enum'


@dc.dataclass(frozen=True)
class SchemaClass:
    class_name: str
    base_type: TypeHint

    allow_extra: bool = False
    has_aliases: bool = False
    docstr: str | None = None
    attributes: list[AttributeModel] = dc.field(default_factory=list)
    model_type: ModelType = ModelType.model

    @property
    def imports(self) -> Iterable[str]:
        yield from self.base_type.imports()
        for prop in self.attributes:
            yield from prop.annotation.type.imports()


@dc.dataclass(frozen=True, kw_only=True)
class SchemaModule(AbstractModule):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for inline request and for response body for each operation
    """

    body: list[SchemaClass] = dc.field(default_factory=list)
    model_type: str = 'schema'

    @property
    def imports(self) -> Iterable[str]:
        for cls in self.body:
            yield from cls.imports
