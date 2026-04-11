from __future__ import annotations

from openapi_pydantic.v3.v3_1 import schema as schema31

from .. import json_pointer, names, runtime
from . import python
from .schemamodel import SchemaModel
from .stack import Stack

FORMAT_ENCODERS = {
    (schema31.DataType.STRING, 'uuid'): python.NameRef(module='uuid', name='UUID'),
    (schema31.DataType.STRING, 'date'): python.NameRef(module='datetime', name='date'),
    (schema31.DataType.STRING, 'date-time'): python.NameRef(module='datetime', name='datetime'),
    (schema31.DataType.STRING, 'time'): python.NameRef(module='datetime', name='time'),
    (schema31.DataType.STRING, 'decimal'): python.NameRef(module='decimal', name='Decimal'),
}


def resolve_type_name(root_package: str, pointer: Stack) -> python.AnnotatedType:
    # FIXME all fields should be saved as json ref; all schemas saved in a map with json ref as a key

    parts = [names.maybe_mangle_name(json_pointer.decode_json_pointer(part)) for part in pointer.path[1:]]
    module_name = '.'.join([root_package, *(part for part in parts[:-1])])
    top = parts[-1]
    return python.AnnotatedType(python.NameRef(module_name, top))


def as_type(model: SchemaModel, root_package: str) -> python.SchemaClass | None:
    """convert schema model, excluding any sub-schemas"""
    if model.any_of or not model.type_ or schema31.DataType.OBJECT not in model.type_ or model.is_any_obj():
        return None

    name = model.stack.top()  # TODO name = value.lapidary_name or stack.top()
    fields = [
        _as_class_field(
            as_annotation(prop_model, root_package, prop_name in model.props_required),
            prop_name,
            prop_name in model.props_required,
        )
        for prop_name, prop_model in model.properties.items()
    ]
    return python.SchemaClass(
        name=names.maybe_mangle_name(name),
        base_type=runtime.ModelBase,
        allow_extra=model.additional_props is not False,
        fields=fields,
        docstr=model.description or None,
    )


def as_annotation(
    model: SchemaModel, root_package: str, required: bool = True, include_object: bool = True
) -> python.AnnotatedType:
    """
    Create type hint for the type represented by the source schema.

    In case where object schema with oneOf or anyOf is used, a type hint for the parent schema is created, and the
    items are rendered in as_type() as a synthetic class field.

    :param model: the schema model to convert
    :param root_package: root python package for object models
    :param required: if false, make the type a Union with None
    :param include_object: if true and the model type includes schema, include the class FQN in the resulting type hint
    """

    if not model.has_annotations():
        return runtime.JsonValue

    if model.any_of:
        return python.union_of(*[as_annotation(t, root_package, required) for t in model.any_of])

    else:
        types: set[python.AnnotatedType] = set()
        for schema_type in model.type_ or ():
            if include_object is False and schema_type == schema31.DataType.OBJECT:
                continue

            match schema_type:
                case schema31.DataType.STRING:
                    try:
                        typ = python.AnnotatedType(FORMAT_ENCODERS[(schema_type, model.format)])  # type: ignore[index]
                    except KeyError:
                        typ = _as_str_anno(model)
                case schema31.DataType.BOOLEAN:
                    typ = python.AnnotatedType.from_type(bool)
                case schema31.DataType.NUMBER:
                    typ = _as_numeric_anno(model, float)
                case schema31.DataType.INTEGER:
                    typ = _as_numeric_anno(model, int)
                case schema31.DataType.NULL:
                    typ = python.NoneMetaType
                case schema31.DataType.OBJECT:
                    typ = _as_object_anno(model, root_package)
                case schema31.DataType.ARRAY:
                    typ = python.list_of(
                        as_annotation(model.items, root_package) if model.items else runtime.JsonValue,
                    )
                case _:
                    raise TypeError(schema_type)
            types.add(typ)

    if not required:
        types.add(python.NoneMetaType)

    return python.union_of(*types)


def _as_class_field(anno: python.AnnotatedType, name: str, required: bool) -> python.AnnotatedVariable:
    python_name = names.maybe_mangle_name(name)
    return python.AnnotatedVariable(
        name=python_name,
        typ=anno,
        alias=name if name != python_name else None,
        required=required,
    )


def _as_numeric_anno(model: SchemaModel, typ: type) -> python.AnnotatedType:
    num_constraints = {'lt', 'gt', 'ge', 'le', 'multiple_of'}
    constraints = {}
    for key in num_constraints:
        if (value := getattr(model, key)) is not None:
            constraints[key] = typ(value)
    return python.AnnotatedType(
        python.NameRef.from_type(typ),
        **constraints,  # type: ignore[arg-type]
    )


def _as_str_anno(model: SchemaModel) -> python.AnnotatedType:
    str_constraints = {'max_length', 'min_length', 'pattern'}
    constraints = {key: value for key in str_constraints if (value := getattr(model, key)) is not None}
    return python.AnnotatedType(
        python.NameRef('builtins', 'str'),
        **constraints,  # type: ignore[arg-type]
    )


def _as_object_anno(model: SchemaModel, root_package: str) -> python.AnnotatedType:
    if not model.properties and not (
        any(sub.properties for sub in model.any_of or () if schema31.DataType.OBJECT in (sub.type_ or ()))
        and any(sub.properties for sub in model.one_of or () if schema31.DataType.OBJECT in (sub.type_ or ()))
    ):
        return runtime.JsonObject
    else:
        return resolve_type_name(root_package, model.stack)
