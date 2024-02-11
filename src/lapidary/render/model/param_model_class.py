"""
Param model is a synthetic (from the perspective of OpenAPI specification) object that holds and validates all Operation
parameters.
"""
from collections.abc import Iterator

from ..names import get_subtype_name
from . import openapi, python
from .refs import ResolverFunc
from .schema_class import get_schema_classes


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
