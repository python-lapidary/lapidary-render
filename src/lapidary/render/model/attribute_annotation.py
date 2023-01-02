from dataclasses import dataclass
from typing import Optional, Any

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import SchemaOrRef, ResolverFunc
from lapidary.runtime.model.type_hint import TypeHint, get_type_hint
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.names import get_subtype_name


@dataclass(frozen=True)
class AttributeAnnotationModel:
    type: TypeHint
    field_props: dict[str, Any]

    default: Optional[str] = None
    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = False


def get_attr_annotation(
        typ: SchemaOrRef,
        name: str,
        parent_name: str,
        required: bool,
        module: ModulePath,
        resolve: ResolverFunc,
        in_: Optional[str] = None,
        alias: Optional[str] = None
) -> AttributeAnnotationModel:
    """
    if typ is a schema, then it's a nested schema. Name should be parent_class_name+prop_name, and module is the same.
    Otherwise, it's a reference; schema, module and name should be resolved from it and used to generate type_ref
    """
    if isinstance(typ, openapi.Reference):
        schema, module, type_name = resolve(typ, openapi.Schema)
    else:
        schema: openapi.Schema = typ
        type_name = get_subtype_name(parent_name, schema.lapidary_name or name)
    return _get_attr_annotation(schema, type_name, required, module, resolve, in_, name, alias)


FIELD_PROPS = {
    'multipleOf': 'multiple_of',
    'maximum': 'le',
    'exclusiveMaximum': 'lt',
    'minimum': 'ge',
    'exclusiveMinimum': 'gt',
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'maxItems': 'max_items',
    'minItems': 'min_items',
    'uniqueItems': 'unique_items',
    'maxProperties': 'max_properties',
    'minProperties': 'min_properties',
}


def _get_attr_annotation(
        schema: openapi.Schema,
        type_name: str,
        required: bool,
        module: ModulePath,
        resolve: ResolverFunc,
        in_: Optional[str],
        name: Optional[str],
        alias: Optional[str],
) -> AttributeAnnotationModel:
    field_props = {FIELD_PROPS[k]: getattr(schema, k) for k in schema.__fields_set__ if k in FIELD_PROPS}
    for k, v in field_props.items():
        if isinstance(v, str):
            field_props[k] = f"'{v}'"

    if in_ is not None:
        field_props['in_'] = 'lapidary.runtime.ParamPlacement.' + in_
        field_props['alias'] = f"'{alias or name}'"

    if alias is not None:
        field_props['alias'] = "'" + alias + "'"

    if 'pattern' in schema.__fields_set__:
        field_props['regex'] = f"r'{schema.pattern}'"

    direction = get_direction(schema.readOnly, schema.writeOnly)
    if direction:
        field_props['direction'] = direction
        # TODO better handle direction
        required = False

    default = None if required else 'lapidary.runtime.absent.ABSENT'

    return AttributeAnnotationModel(
        type=get_type_hint(schema, module, type_name, required, resolve),
        default=default,
        field_props=field_props
    )


def get_direction(read_only: Optional[bool], write_only: Optional[bool]) -> Optional[str]:
    if read_only:
        if write_only:
            raise ValueError()
        else:
            return 'lapidary.runtime.ParamDirection.read'
    else:
        if write_only:
            return 'lapidary.runtime.ParamDirection.write'
        else:
            return None
