from . import openapi, python
from .attribute import get_enum_attribute


def get_enum_class(schema: openapi.Schema, name: str):
    enum_fields = []
    for v in schema.enum:
        try:
            enum_fields.append(get_enum_attribute(v, schema.lapidary_names.get(v, v)))
        except Exception as error:
            raise ValueError(f"Could not prepare enum field for value '{v}' of {name}") from error
    return python.SchemaClass(
        class_name=name,
        base_type=python.TypeHint.from_str('enum:Enum'),
        attributes=enum_fields,
        docstr=schema.description or None,
        model_type=python.ModelType.enum,
    )
