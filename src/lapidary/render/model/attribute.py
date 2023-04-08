from dataclasses import dataclass
from typing import Any, Optional, Union

from lapidary.runtime import openapi
from lapidary.runtime.model import ResolverFunc, from_type
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.names import check_name, maybe_mangle_name, get_enum_field_name

from .attribute_annotation import AttributeAnnotationModel, get_attr_annotation


@dataclass(frozen=True)
class AttributeModel:
    name: str
    annotation: AttributeAnnotationModel
    deprecated: bool = False
    """Currently not used"""

    required: Optional[bool] = None
    """
    Used for op method params. Required params are rendered before optional, and optional have default value ABSENT
    """


def get_attributes(
        parent_schema: openapi.Schema, parent_class_name: str, module: ModulePath, resolver: ResolverFunc
) -> list[AttributeModel]:
    def is_required(schema: openapi.Schema, prop_name: str) -> bool:
        return schema.required is not None and prop_name in schema.required

    return [
        get_attribute(
            prop_schema,
            parent_schema.lapidary_names.get(name, name),
            name if parent_schema.lapidary_names.get(name, name) != name else None,
            parent_class_name,
            is_required(parent_schema, name),
            module,
            resolver,
        )
        for name, prop_schema in parent_schema.properties.items()
    ]


def get_attribute(
        typ: Union[openapi.Schema, openapi.Reference], name: str, alias: str, parent_name: str, required: bool, module: ModulePath,
        resolve: ResolverFunc
) -> AttributeModel:
    alias = alias or name
    name = maybe_mangle_name(name, False)
    check_name(name, False)
    alias = alias if alias != name else None

    return AttributeModel(
        name=name,
        annotation=get_attr_annotation(typ, name, parent_name, required, module, resolve, alias=alias),
    )


def get_enum_attribute(value: Any, name: Optional[str]) -> AttributeModel:
    if isinstance(value, str):
        quoted_value = "'" + value.replace("'", r"\'") + "'" if value is not None else None
    else:
        quoted_value = value
    return AttributeModel(
        name=maybe_mangle_name(name, False) if name else get_enum_field_name(value),
        annotation=AttributeAnnotationModel(
            type=from_type(type(value)),
            field_props={'default': quoted_value},
        )
    )
