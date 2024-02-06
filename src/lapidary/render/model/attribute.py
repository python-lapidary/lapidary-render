import typing

from ..names import check_name, get_enum_field_name, maybe_mangle_name
from . import python
from .attribute_annotation import get_attr_annotation
from .openapi import model
from .refs import ResolverFunc


def get_attributes(
    parent_schema: model.Schema, parent_class_name: str, module: python.ModulePath, resolver: ResolverFunc
) -> list[python.AttributeModel]:
    def is_required(schema: model.Schema, prop_name: str) -> bool:
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
    typ: model.Schema | model.Reference,
    name: str,
    alias: str,
    parent_name: str,
    required: bool,
    module: python.ModulePath,
    resolve: ResolverFunc,
) -> python.AttributeModel:
    alias = alias or name
    name = maybe_mangle_name(name, False)
    check_name(name, False)
    alias = alias if alias != name else None

    return python.AttributeModel(
        name=name,
        annotation=get_attr_annotation(typ, name, parent_name, required, module, resolve, alias=alias),
    )


def get_enum_attribute(value: typing.Any, name: str | None) -> python.AttributeModel:
    if isinstance(value, str):
        quoted_value = "'" + value.replace("'", r'\'') + "'" if value is not None else None
    else:
        quoted_value = value
    return python.AttributeModel(
        name=maybe_mangle_name(name, False) if name else get_enum_field_name(value),
        annotation=python.AttributeAnnotationModel(
            type=python.TypeHint.from_type(type(value)),
            field_props={'default': quoted_value},
        ),
    )
