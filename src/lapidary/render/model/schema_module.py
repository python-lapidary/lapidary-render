import logging
import typing

from ..names import (
    PARAM_MODEL,
    REQUEST_BODY,
    RESPONSE_BODY,
    check_name,
    get_schema_module_name,
)
from . import openapi, python
from .param_model_class import get_param_model_classes
from .python.module import template_imports
from .refs import ResolverFunc
from .request_body import get_request_body_module
from .response_body import get_response_body_module
from .schema_class import get_schema_classes

logger = logging.getLogger(__name__)


def get_modules_for_components_schemas(
        schemas: dict[str, openapi.Schema | openapi.Reference], root_package: python.ModulePath, resolver: ResolverFunc
) -> list[python.SchemaModule]:
    modules = []
    for name, schema in schemas.items():
        if isinstance(schema, openapi.Schema):
            name = schema.lapidary_name or name
            check_name(name)
            module = get_schema_module(schema, name, root_package / get_schema_module_name(name), resolver)
            if module is not None:
                modules.append(module)
    return modules


def get_schema_module(
        schema: openapi.Schema, name: str, path: python.ModulePath, resolver: ResolverFunc
) -> python.SchemaModule | None:
    classes = [cls for cls in get_schema_classes(schema, name, path, resolver)]
    if len(classes) > 0:
        return _get_schema_module(classes, path)


def _get_schema_module(classes: list[python.SchemaClass], path: python.ModulePath, model_type="schema") -> python.SchemaModule:
    imports = {
        imp
        for cls in classes
        if cls.base_type is not None
        for imp in cls.base_type.imports()
        if imp not in template_imports
    }

    imports.update({
        import_
        for schema_class in classes
        for attr in schema_class.attributes
        for import_ in attr.annotation.type.imports()
        if import_ not in imports and import_ not in template_imports and import_ != str(path)
    })
    imports = sorted(imports)

    return python.SchemaModule(
        path=path,
        body=classes,
        imports=imports,
        model_type=model_type,
    )


def get_param_model_classes_module(op: openapi.Operation, module: python.ModulePath, resolve: ResolverFunc) -> python.SchemaModule:
    classes = [cls for cls in get_param_model_classes(op, module, resolve)]
    return _get_schema_module(classes, module, "param_model")


def get_schema_modules(model: openapi.OpenApiModel, root_module: python.ModulePath, resolver: ResolverFunc) -> typing.Iterable[python.SchemaModule]:
    if model.components and model.components.schemas:
        logger.info('Render schema modules')
        path = root_module / 'components' / 'schemas'
        yield from get_modules_for_components_schemas(model.components.schemas, path, resolver)

    for path, path_item in model.paths.items():
        for tpl in openapi.get_operations(path_item, True):
            _, op = tpl
            op_root_module = root_module / 'paths' / op.operationId
            if op.parameters:
                mod = get_param_model_classes_module(op, op_root_module / PARAM_MODEL, resolver)
                if len(mod.body) > 0:
                    yield mod
            if op.requestBody:
                mod = get_request_body_module(op, op_root_module / REQUEST_BODY, resolver)
                if len(mod.body) > 0:
                    yield mod
            if len(op.responses.items()):
                mod = get_response_body_module(op, op_root_module / RESPONSE_BODY, resolver)
                if len(mod.body) > 0:
                    yield mod
