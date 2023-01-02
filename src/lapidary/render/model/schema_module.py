from dataclasses import dataclass, field
from typing import Union, Optional

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.names import check_name, get_schema_module_name

from .module import AbstractModule, template_imports
from .param_model_class import get_param_model_classes
from .schema_class import get_schema_classes
from .schema_class_model import SchemaClass


@dataclass(frozen=True, kw_only=True)
class SchemaModule(AbstractModule):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for inline request and for response body for each operation
    """
    body: list[SchemaClass] = field(default_factory=list)


def get_modules_for_components_schemas(
        schemas: dict[str, Union[openapi.Schema, openapi.Reference]], root_package: ModulePath, resolver: ResolverFunc
) -> list[SchemaModule]:
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
        schema: openapi.Schema, name: str, path: ModulePath, resolver: ResolverFunc
) -> Optional[SchemaModule]:
    classes = [cls for cls in get_schema_classes(schema, name, path, resolver)]
    if len(classes) > 0:
        return _get_schema_module(classes, path)


def _get_schema_module(classes: list[SchemaClass], path: ModulePath) -> SchemaModule:
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
        if import_ not in imports and import_ not in template_imports and import_ != path.str()
    })
    imports = sorted(imports)

    return SchemaModule(
        path=path,
        body=classes,
        imports=imports,
    )


def get_param_model_classes_module(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> SchemaModule:
    classes = [cls for cls in get_param_model_classes(op, module, resolve)]
    return _get_schema_module(classes, module)
