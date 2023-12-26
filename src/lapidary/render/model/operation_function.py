import logging
import warnings
from dataclasses import dataclass
from typing import Optional, Union

from lapidary.runtime import openapi
from lapidary.runtime.model import TypeHint, resolve_type_hint, GenericTypeHint, from_type
from lapidary.runtime.model.params import ParamLocation, get_param_type
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.model.type_hint import UnionTypeHint
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.names import get_param_python_name, escape_name, PARAM_MODEL

from .attribute import AttributeModel
from .attribute_annotation import AttributeAnnotationModel
from .request_body import get_request_body_type

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OperationFunctionModel:
    name: str
    request_type: Optional[TypeHint]
    params: list[AttributeModel]
    response_type: Optional[TypeHint]
    auth_name: Optional[str]
    docstr: Optional[str] = None


_FIELD_PROPS = dict(
    in_=None,
    description=None,
    allowEmptyValue=False,
    style=None,
    explode=None,
    allowReserved=False,
)


def get_operation_param(
        param: Union[openapi.Parameter, openapi.Reference], module: ModulePath, resolve: ResolverFunc
) -> AttributeModel:
    if isinstance(param, openapi.Reference):
        param, module, _ = resolve(param, openapi.Parameter)

    return get_operation_param_(param, module, resolve)


def get_operation_param_(
        param: openapi.Parameter, parent_module: ModulePath, resolve: ResolverFunc
) -> AttributeModel:
    field_props = {k: getattr(param, k, default) for k, default in _FIELD_PROPS.items()}
    param_name = get_param_python_name(param)

    return AttributeModel(
        name=param_name,
        annotation=AttributeAnnotationModel(
            type=get_param_type(param, parent_module, resolve),
            field_props=field_props,
        ),
        deprecated=param.deprecated,
        required=param.required,
    )


def get_operation_func(
        op: openapi.Operation, parent: ModulePath, resolver: ResolverFunc
) -> OperationFunctionModel:
    if not op.operationId:
        raise ValueError('operationId is required')

    module = parent / op.operationId

    params = []
    if op.parameters:
        params_module = module / PARAM_MODEL
        for oapi_param in op.parameters:
            if oapi_param.in_ == ParamLocation.header.value and oapi_param.name.lower() in [
                'accept', 'content-type', 'authorization'
            ]:
                warnings.warn(f'Header param "{oapi_param.name}" ignored')
                continue
            try:
                params.append(get_operation_param(oapi_param, params_module, resolver))
            except Exception:
                raise Exception("Error while handling parameter", oapi_param.name)

    request_type = get_request_body_type(op, module, resolver) if op.requestBody else None

    response_types = get_response_types(op, module, resolver)
    if len(response_types) == 0:
        response_type = None
    elif len(response_types) == 1:
        response_type = response_types.pop()
    else:
        response_type = UnionTypeHint.of(*response_types)

    auth_name = None
    if op.security is not None and len(op.security) > 0:
        requirement = next(iter(op.security)).__root__
        if len(requirement) > 0:
            auth_name = next(iter(requirement.keys()))

    return OperationFunctionModel(
        name=op.operationId,
        request_type=request_type,
        params=params,
        response_type=response_type,
        auth_name=auth_name,
    )


def get_response_types(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> set[TypeHint]:
    """
    Generate unique collection of types that may be returned by the operation. Skip types that are marked as exceptions as those are raised instead.
    """

    return get_response_types_(op.responses, module, resolve)


def get_response_types_(responses: openapi.Responses, module: ModulePath, resolve: ResolverFunc) -> set[TypeHint]:
    response_types = set()
    for resp_code, response in responses.items():
        if isinstance(response, openapi.Reference):
            response, module, name = resolve(response, openapi.Response)
        if response.content is None:
            continue
        for _media_type_name, media_type in response.content.items():
            schema = media_type.schema_
            if isinstance(schema, openapi.Reference):
                schema, resp_module, name = resolve(schema, openapi.Schema)
            else:
                name = "schema"
                resp_module = module / "responses" / escape_name(str(resp_code)) / "content" / escape_name(_media_type_name)
            if schema.lapidary_model_type is openapi.LapidaryModelType.EXCEPTION:
                continue
            typ = resolve_type_hint(schema, resp_module, name, resolve)

            if schema.lapidary_model_type is openapi.LapidaryModelType.ITERATOR:
                typ = to_iterator(typ)

            response_types.add(typ)
    return response_types


def to_iterator(type_: TypeHint) -> TypeHint:
    if not isinstance(type_, GenericTypeHint):
        return type_

    if type_.origin == from_type(Union):
        return UnionTypeHint.of(*(to_iterator(targ) for targ in type_.args))

    if type_.origin == from_type(list):
        return GenericTypeHint(module='collections.abc', type_name='Iterator', args=type_.args)

    return type_
