"""
Param model is a synthetic (from the perspective of OpenAPI specification) object that holds and validates all Operation
parameters.
"""
from collections.abc import Iterator

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.names import get_subtype_name, check_name, get_param_python_name

from .attribute import AttributeModel
from .attribute_annotation import get_attr_annotation
from .schema_class import get_schema_classes
from .schema_class_model import SchemaClass


def get_param_attribute(
        param: openapi.Parameter,
        parent_name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> AttributeModel:
    attr_name = get_param_python_name(param)
    check_name(attr_name)

    return AttributeModel(
        name=attr_name,
        annotation=get_attr_annotation(
            param.schema_, param.name, parent_name, param.required, module, resolver, param.in_
        ),
        deprecated=param.deprecated,
    )


def get_param_model_classes(
        operation: openapi.Operation,
        module: ModulePath,
        resolver: ResolverFunc,
) -> Iterator[SchemaClass]:
    # handle sub schemas
    for param in operation.parameters:
        schema = param.schema_
        if not isinstance(schema, openapi.Schema):
            continue
        param_name = param.lapidary_name or param.name
        yield from get_schema_classes(schema, get_subtype_name(operation.operationId, param_name), module, resolver)
