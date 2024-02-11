import logging
import warnings

from ..names import PARAM_MODEL, escape_name, param_model_name
from . import openapi, python
from .params import get_param_type
from .refs import ResolverFunc
from .request_body import get_request_body_type
from .type_hint import resolve_type_hint

logger = logging.getLogger(__name__)

_FIELD_PROPS = dict(
    in_=None,
    description=None,
    allowEmptyValue=False,
    style=None,
    explode=None,
    allowReserved=False,
)


def get_operation_param(
    param: openapi.Parameter | openapi.Reference, module: python.ModulePath, resolve: ResolverFunc
) -> python.attribute.AttributeModel:
    if isinstance(param, openapi.Reference):
        param, module, _ = resolve(param, openapi.Parameter)

    return get_operation_param_(param, module, resolve)


def get_operation_param_(
    param: openapi.Parameter, parent_module: python.ModulePath, resolve: ResolverFunc
) -> python.attribute.AttributeModel:
    field_props = {k: getattr(param, k, default) for k, default in _FIELD_PROPS.items()}
    param_name = param_model_name(param)

    return python.attribute.AttributeModel(
        name=param_name,
        annotation=python.attribute.AttributeAnnotationModel(
            type=get_param_type(param, parent_module, resolve),
            field_props=field_props,
        ),
        deprecated=param.deprecated,
        required=param.required,
    )


def get_operation_func(
    op: openapi.Operation, parent: python.ModulePath, resolver: ResolverFunc
) -> python.OperationFunctionModel:
    if not op.operationId:
        raise ValueError('operationId is required')

    module = parent / op.operationId

    params = []
    if op.parameters:
        params_module = module / PARAM_MODEL
        for oapi_param in op.parameters:
            if oapi_param.in_ == python.ParamLocation.header.value and oapi_param.name.lower() in (
                'accept',
                'content-type',
                'authorization',
            ):
                warnings.warn(f'Header param "{oapi_param.name}" ignored')
                continue
            try:
                params.append(get_operation_param(oapi_param, params_module, resolver))
            except Exception:
                raise Exception('Error while handling parameter', oapi_param.name)

    request_type = get_request_body_type(op, module, resolver) if op.requestBody else None

    response_types = get_response_types(op, module, resolver)
    if len(response_types) == 0:
        response_type = None
    elif len(response_types) == 1:
        response_type = response_types.pop()
    else:
        response_type = python.type_hint.GenericTypeHint.union_of(tuple(response_types))

    auth_name = None
    if op.security is not None and len(op.security) > 0:
        requirement = next(iter(op.security)).__root__
        if len(requirement) > 0:
            auth_name = next(iter(requirement.keys()))

    return python.OperationFunctionModel(
        name=op.operationId,
        request_type=request_type,
        params=params,
        response_type=response_type,
        auth_name=auth_name,
    )


def get_response_types(op: openapi.Operation, module: python.ModulePath, resolve: ResolverFunc) -> set[python.TypeHint]:
    """
    Generate unique collection of types that may be returned by the operation. Skip types that are marked as exceptions as those are raised instead.
    """

    response_types = set()
    for resp_code, response in op.responses.responses.items():
        if isinstance(response, openapi.Reference):
            response, module, name = resolve(response, openapi.Response)
        if response.content is None:
            continue
        for _media_type_name, media_type in response.content.items():
            schema = media_type.schema_
            if isinstance(schema, openapi.Reference):
                schema, resp_module, name = resolve(schema, openapi.Schema)
            else:
                name = 'schema'
                resp_module = module / 'responses' / escape_name(resp_code) / 'content' / escape_name(_media_type_name)
            if schema.lapidary_model_type is openapi.LapidaryModelType.exception:
                continue
            typ = resolve_type_hint(schema, resp_module, name, resolve)

            response_types.add(typ)
    return response_types
