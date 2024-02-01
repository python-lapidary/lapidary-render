from . import get_enum_attribute, openapi
from .python.type_hint import TypeHint
from .schema_class_model import ModelType, SchemaClass


def get_enum_class(
        schema: openapi.Schema,
        name: str
):
    enum_fields = []
    for v in schema.enum:
        try:
            enum_fields.append(get_enum_attribute(v, schema.lapidary_names.get(v, v)))
        except Exception as error:
            raise ValueError(f"Could not prepare enum field for value '{v}' of {name}") from error
    return SchemaClass(
        class_name=name,
        base_type=TypeHint.from_str('enum:Enum'),
        attributes=enum_fields,
        docstr=schema.description or None,
        model_type=ModelType.enum,
    )
