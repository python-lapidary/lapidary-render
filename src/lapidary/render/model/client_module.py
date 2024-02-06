import itertools
import logging

from . import openapi
from .client_class import get_client_class
from .python import ClientModule, ModulePath
from .python.module import template_imports
from .refs import ResolverFunc

logger = logging.getLogger(__name__)


def get_client_class_module(
    model: openapi.OpenApiModel,
    client_module: ModulePath,
    root_module: ModulePath,
    resolver: ResolverFunc,
) -> ClientModule:
    client_class = get_client_class(model, root_module, resolver)

    default_imports = [
        'lapidary.runtime',
        'httpx',
    ]

    global_response_type_imports = {
        import_ for type_hint in client_class.init_method.response_types for import_ in type_hint.imports()
    }

    request_response_type_imports = {
        import_
        for func in client_class.methods
        for imports in itertools.chain(
            map(
                lambda elem: elem.imports(),
                filter(lambda elem: elem is not None, (func.response_type, func.request_type)),
            )
        )
        for import_ in imports
    }

    param_type_imports = {
        imp
        for attr in client_class.methods
        for t in attr.params
        for imp in t.annotation.type.imports()
        if imp not in default_imports and imp not in template_imports
    }

    imports = list(
        {
            *default_imports,
            *global_response_type_imports,
            *request_response_type_imports,
            *param_type_imports,
        }
    )

    imports.sort()

    return ClientModule(
        path=client_module,
        imports=imports,
        body=client_class,
    )
