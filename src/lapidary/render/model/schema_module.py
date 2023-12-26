import dataclasses as dc
import logging
import typing as ty

from lapidary.runtime import names as mod_name, openapi
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.module_path import ModulePath

from .module import AbstractModule, template_imports
from .param_model_class import get_param_model_classes
from .request_body import get_request_body_module
from .response_body import get_response_body_module
from .schema_class import get_schema_classes
from .schema_class_model import SchemaClass

logger = logging.getLogger(__name__)


@dc.dataclass(frozen=True, kw_only=True)
class SchemaModule(AbstractModule):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for inline request and for response body for each operation
    """
    body: list[SchemaClass] = dc.field(default_factory=list)
    model_type: str = 'schema'


def get_modules_for_components_schemas(
        schemas: dict[str, ty.Union[openapi.Schema, openapi.Reference]], root_package: ModulePath, resolver: ResolverFunc
) -> list[SchemaModule]:
    modules = []
    for name, schema in schemas.items():
        if isinstance(schema, openapi.Schema):
            name = schema.lapidary_name or name
            mod_name.check_name(name)
            module = get_schema_module(schema, name, root_package / mod_name.get_schema_module_name(name), resolver)
            if module is not None:
                modules.append(module)
    return modules


def get_schema_module(
        schema: openapi.Schema, name: str, path: ModulePath, resolver: ResolverFunc
) -> ty.Optional[SchemaModule]:
    classes = [cls for cls in get_schema_classes(schema, name, path, resolver)]
    if len(classes) > 0:
        return _get_schema_module(classes, path)


def _get_schema_module(classes: list[SchemaClass], path: ModulePath, model_type="schema") -> SchemaModule:
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

    return SchemaModule(
        path=path,
        body=classes,
        imports=imports,
        model_type=model_type,
    )


def get_param_model_classes_module(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> SchemaModule:
    classes = [cls for cls in get_param_model_classes(op, module, resolve)]
    return _get_schema_module(classes, module, "param_model")


def get_schema_modules(model: openapi.OpenApiModel, root_module: ModulePath, resolver: ResolverFunc) -> ty.Iterable[SchemaModule]:
    if model.components and model.components.schemas:
        logger.info('Render schema modules')
        path = root_module / 'components' / 'schemas'
        yield from get_modules_for_components_schemas(model.components.schemas, path, resolver)

    for path, path_item in model.paths.items():
        for tpl in openapi.get_operations(path_item, True):
            _, op = tpl
            op_root_module = root_module / 'paths' / op.operationId
            if op.parameters:
                mod = get_param_model_classes_module(op, op_root_module / mod_name.PARAM_MODEL, resolver)
                if len(mod.body) > 0:
                    yield mod
            if op.requestBody:
                mod = get_request_body_module(op, op_root_module / mod_name.REQUEST_BODY, resolver)
                if len(mod.body) > 0:
                    yield mod
            if len(op.responses.items()):
                mod = get_response_body_module(op, op_root_module / mod_name.RESPONSE_BODY, resolver)
                if len(mod.body) > 0:
                    yield mod
