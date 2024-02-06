"""
Param model is a synthetic (from the perspective of OpenAPI specification) object that holds and validates all Operation
parameters.
"""
from collections.abc import Iterator

from ..names import check_name, get_param_python_name, get_subtype_name
from . import openapi, python
from .attribute_annotation import get_attr_annotation
from .refs import ResolverFunc
from .schema_class import get_schema_classes


def get_param_attribute(
    param: openapi.Parameter,
    parent_name: str,
    module: python.ModulePath,
    resolver: ResolverFunc,
) -> python.AttributeModel:
    attr_name = get_param_python_name(param)
    check_name(attr_name)

    return python.AttributeModel(
        name=attr_name,
        annotation=get_attr_annotation(
            param.schema_, param.name, parent_name, param.required, module, resolver, param.in_
        ),
        deprecated=param.deprecated,
    )


def get_param_model_classes(
    operation: openapi.Operation,
    module: python.ModulePath,
    resolver: ResolverFunc,
) -> Iterator[python.SchemaClass]:
    # handle sub schemas
    for param in operation.parameters:
        schema = param.schema_
        if not isinstance(schema, openapi.Schema):
            continue
        param_name = param.lapidary_name or param.name
        yield from get_schema_classes(schema, get_subtype_name(operation.operationId, param_name), module, resolver)
