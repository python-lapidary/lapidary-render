from dataclasses import dataclass
from typing import Optional, Union

from .attribute import AttributeModel, get_attribute
from ..refs import ResolverFunc
from ...openapi import model as openapi


@dataclass(frozen=True)
class SchemaClass:
    class_name: str
    attributes: dict[str, AttributeModel]
    docstr: Optional[str]


def get_schema_class(
        schema: Union[openapi.Schema, openapi.Reference],
        path: list[str],
        resolver: ResolverFunc,
) -> SchemaClass:
    if isinstance(schema, openapi.Reference):
        schema, path = resolver(schema)
    attributes = {attr_name: get_attribute(attr, schema.required and attr_name in schema.required, [*path, attr_name], resolver) for attr_name, attr in
                  schema.properties.items()} if schema.properties else {}

    return SchemaClass(
        class_name=path[-1],
        attributes=attributes,
        docstr=schema.description or None,
    )