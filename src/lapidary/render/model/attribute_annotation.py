from . import openapi, python
from .context import Context
from .stack import Stack
from .type_hint import get_type_hint


def get_attr_annotation(
    ctx: Context,
    stack: Stack,
    value: openapi.Schema | openapi.Reference[openapi.Schema],
    required: bool,
) -> python.AttributeAnnotationModel:
    """
    if typ is a schema, then it's a nested schema. Name should be parent_class_name+prop_name, and module is the same.
    Otherwise, it's a reference; schema, module and name should be resolved from it and used to generate type_ref
    """
    if isinstance(value, openapi.Reference):
        return get_attr_annotation(ctx, *ctx.resolve_ref(value))

    name = stack.top()

    field_props = {FIELD_PROPS[k]: getattr(value, k) for k in value.model_fields_set if k in FIELD_PROPS}
    for k, v in field_props.items():
        if isinstance(v, str):
            field_props[k] = f"'{v}'"

    # if schema.in_ is not None:
    #     field_props['in_'] = 'lapidary.runtime.ParamPlacement.' + schema.in_
    #     field_props['alias'] = f"'{schema.lapidary_name or name}'"

    if name is not None:
        field_props['alias'] = "'" + name + "'"

    if 'pattern' in value.model_fields_set:
        field_props['regex'] = f"r'{value.pattern}'"

    direction = get_direction(value.readOnly, value.writeOnly)
    if direction:
        field_props['direction'] = direction
        # TODO better handle direction
        # required = False

    default = None if value.required else 'lapidary.runtime.absent.ABSENT'

    return python.attribute.AttributeAnnotationModel(
        type=get_type_hint(ctx, stack, value), default=default, field_props=field_props
    )


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
