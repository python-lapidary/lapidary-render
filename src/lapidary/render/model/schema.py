import logging

from .. import names
from . import openapi, python
from .context import Context
from .stack import Stack
from .type_hint import get_type_hint

logger = logging.getLogger(__name__)


class OpenApi30SchemaConverter:
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx

    def process_schema(
        self,
        stack: Stack,
        value: openapi.Schema,
    ) -> python.TypeHint:
        logger.debug('process schema %s', stack)

        if isinstance(value, openapi.Reference):
            return self.process_schema(*self.ctx.resolve_ref(value))

        assert isinstance(value, openapi.Schema)

        name = value.lapidary_name or stack.top()

        path = str(stack)
        if path not in self.ctx.schema_types:
            base_type = (
                python.TypeHint.from_type(Exception)
                if value.lapidary_model_type is openapi.LapidaryModelType.exception
                else python.TypeHint.from_str('pydantic:BaseModel')
            )

            stack_attr = stack.push('properties')
            attributes = [
                self.process_property(stack_attr.push(prop_name), prop_schema, prop_name in value.required)
                for prop_name, prop_schema in value.properties.items()
            ]

            self.ctx.schema_types[stack] = python.SchemaClass(
                class_name=name,
                base_type=base_type,
                allow_extra=value.additionalProperties is not False,
                has_aliases=any(['alias' in attr.annotation.field_props for attr in attributes]),
                attributes=attributes,
                docstr=value.description or None,
                model_type=python.ModelType[value.lapidary_model_type.name]
                if value.lapidary_model_type
                else python.ModelType.model,
            )

        return get_type_hint(self.ctx, stack, value)

    def process_property(
        self,
        stack: Stack,
        value: openapi.Schema | openapi.Reference[openapi.Schema],
        required: bool,
    ) -> python.AttributeModel:
        alias = value.lapidary_name or names.maybe_mangle_name(stack.top())
        names.check_name(alias, False)

        return python.AttributeModel(
            name=alias,
            annotation=self.get_attr_annotation(stack, value, required),
        )

    def get_attr_annotation(
        self,
        stack: Stack,
        value: openapi.Schema | openapi.Reference[openapi.Schema],
        required: bool,
    ) -> python.AttributeAnnotationModel:
        """
        if typ is a schema, then it's a nested schema. Name should be parent_class_name+prop_name, and module is the same.
        Otherwise, it's a reference; schema, module and name should be resolved from it and used to generate type_ref
        """
        if isinstance(value, openapi.Reference):
            return self.get_attr_annotation(*self.ctx.resolve_ref(value))

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

        return python.AttributeAnnotationModel(
            type=get_type_hint(self.ctx, stack, value), default=default, field_props=field_props
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
