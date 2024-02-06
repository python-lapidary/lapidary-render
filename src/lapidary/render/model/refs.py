from __future__ import annotations

import functools
import logging
import typing

if typing.TYPE_CHECKING:
    from . import openapi, python

logger = logging.getLogger(__name__)

T = typing.TypeVar(
    'T',
    'openapi.Schema',
    'openapi.Parameter',
    'openapi.SecurityScheme',
    'openapi.Response',
    'openapi.Operation',
)
ResolverFunc = typing.Callable[['openapi.Reference', type[T]], tuple[T, 'python.ModulePath', str]]


def resolve(
    model: openapi.OpenApiModel,
    root_package: str,
    ref: openapi.Reference,
    typ: type[T],
) -> tuple[T, python.ModulePath, str]:
    """
    module = {root_package}.{path[0:4]}
    name = path[4:]
    """

    from . import openapi, python

    path = ref_to_path(recursive_resolve(model, ref.ref))

    if path[0] == 'paths':
        op = resolve_ref(model, _mkref(path[:4]), openapi.Operation)
        if op.operationId:
            path[2:4] = op.operationId

    module = python.ModulePath(root_package) / path[:-1]
    result = resolve_ref(model, _mkref(path), typ)
    assert isinstance(result, typ)
    return result, module, path[-1]


def get_resolver(model: openapi.OpenApiModel, package: str) -> ResolverFunc:
    return typing.cast(ResolverFunc, functools.partial(resolve, model, package))


def _mkref(s: list[str]) -> str:
    return '/'.join(['#', *s])


def ref_to_path(ref: str) -> list[str]:
    return ref.split('/')[1:]


def resolve_ref(model: openapi.OpenApiModel, ref: str, t: type[T] = typing.Any) -> T:
    result = _schema_get(model, recursive_resolve(model, ref))
    if not isinstance(result, t):
        raise TypeError(ref, t, type(result))
    else:
        return result


def recursive_resolve(model: openapi.OpenApiModel, ref: str) -> str:
    """
    Resolve recursive references
    :return: The last reference, which points to a non-reference object
    """

    from . import openapi

    stack = [ref]

    while True:
        obj = _schema_get(model, ref)
        if isinstance(obj, openapi.Reference):
            ref = obj.ref
            if ref in stack:
                raise RecursionError(stack, ref)
            else:
                stack.append(ref)
        else:
            return ref


def _schema_get(model: openapi.OpenApiModel, ref: str) -> typing.Any:
    path = ref_to_path(ref)
    for part in path:
        model = model[part] if isinstance(model, typing.Mapping) else getattr(model, part)
    return model
