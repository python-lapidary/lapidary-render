from ..names import get_subtype_name
from . import openapi, python
from .refs import ResolverFunc
from .type_hint import get_type_hint


def get_attr_annotation(
        typ: openapi.SchemaOrRef,
        name: str,
        parent_name: str,
        required: bool,
        module: python.ModulePath,
        resolve: ResolverFunc,
        in_: str | None = None,
        alias: str | None = None
) -> python.AttributeAnnotationModel:
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
        module: python.ModulePath,
        resolve: ResolverFunc,
        in_: str | None,
        name: str | None,
        alias: str | None,
) -> python.attribute.AttributeAnnotationModel:
    field_props = {FIELD_PROPS[k]: getattr(schema, k) for k in schema.model_fields_set if k in FIELD_PROPS}
    for k, v in field_props.items():
        if isinstance(v, str):
            field_props[k] = f"'{v}'"

    if in_ is not None:
        field_props['in_'] = 'lapidary.runtime.ParamPlacement.' + in_
        field_props['alias'] = f"'{alias or name}'"

    if alias is not None:
        field_props['alias'] = "'" + alias + "'"

    if 'pattern' in schema.model_fields_set:
        field_props['regex'] = f"r'{schema.pattern}'"

    direction = get_direction(schema.readOnly, schema.writeOnly)
    if direction:
        field_props['direction'] = direction
        # TODO better handle direction
        required = False

    default = None if required else 'lapidary.runtime.absent.ABSENT'

    return python.attribute.AttributeAnnotationModel(
        type=get_type_hint(schema, module, type_name, required, resolve),
        default=default,
        field_props=field_props
    )


def get_direction(read_only: bool | None, write_only: bool | None) -> str | None:
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
