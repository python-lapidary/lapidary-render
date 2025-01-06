from __future__ import annotations

import dataclasses as dc
import itertools
import operator
from collections.abc import Callable, Collection, Container
from typing import Any, Self

from openapi_pydantic.v3.v3_1 import schema as schema31

from .. import json_pointer, names
from ..runtime import AnyJsonType, ModelBase
from . import python
from .python import AnnotatedType
from .stack import Stack


def not_none_or[T](a: T | None, b: T | None, fn: Callable[[T, T], T]) -> T | None:
    """
    If neither a or b is None, return the result of fn,
    If one of them is None, return the other,
    otherwise return None
    """
    if a is None:
        return b
    else:
        return a if b is None else fn(a, b)


def same_or_raise[T](field: str) -> Callable[[T, T], T]:
    def _(a: T, b: T) -> T:
        if a != b:
            raise ValueError('Unsupported values', field, a, b)

        return a

    return _


@dc.dataclass(kw_only=True)
class MetaModel:
    # used to generate package, module and class name
    stack: Stack

    # if not required, join the python type in union with None and add default value None
    required: bool = True

    title: str | None = None
    description: str | None = None

    type_: set[schema31.DataType] | None = None
    enum: set[Any] | None = None
    read_only: bool = False
    write_only: bool = False

    gt: float | None = None
    ge: float | None = None
    lt: float | None = None
    le: float | None = None
    multiple_of: float | None = None

    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    format: str | None = None

    properties: dict[str, MetaModel] = dc.field(default_factory=dict)
    additional_props: MetaModel | bool = True
    props_required: Container[str] = dc.field(default_factory=set)

    items: MetaModel | None = None

    any_of: list[MetaModel] | None = None
    one_of: list[MetaModel] | None = None
    all_of: list[MetaModel] | None = None
    not_: MetaModel | None = None

    def normalize_model(self) -> MetaModel | None:
        if self.type_ is None:
            self.type_ = {typ for typ in schema31.DataType if typ is not schema31.DataType.NULL}

        # merge allOf
        model: MetaModel | None = self
        for schema in self.all_of or ():
            if model is None:
                break
            model &= schema

        return model

    def _only_constraints(self) -> Self:
        return dc.replace(
            self,
            any_of=None,
            all_of=None,
            one_of=None,
            not_=None,
        )

    def __and__(self, other) -> MetaModel | None:
        if other is None or other is False:
            return None
        if other is True:
            return self
        if not isinstance(other, MetaModel):
            return NotImplemented

        model = dc.replace(self)

        model.type_ = not_none_or(self.type_, other.type_, operator.and_)

        model.enum = not_none_or(self.enum, other.enum, operator.and_)
        model.gt = not_none_or(self.gt, other.gt, min)
        model.ge = not_none_or(self.ge, other.ge, min)
        model.lt = not_none_or(self.lt, other.lt, max)
        model.le = not_none_or(self.le, other.le, max)

        if isinstance(self.multiple_of, float) and isinstance(self.multiple_of, float):
            raise NotImplementedError
        model.multiple_of = self.multiple_of or other.multiple_of

        model.min_length = not_none_or(self.min_length, other.min_length, max)
        model.max_length = not_none_or(self.min_length, other.min_length, min)
        model.pattern = not_none_or(self.pattern, other.pattern, same_or_raise('pattern'))
        model.format = not_none_or(self.format, other.format, same_or_raise('format'))

        model.properties = self._properties_and(other)

        if isinstance(self.additional_props, bool) and isinstance(other.additional_props, bool):
            model.additional_props = self.additional_props and other.additional_props
        else:
            self_schema = (
                self.additional_props
                if isinstance(self.additional_props, MetaModel)
                else MetaModel(stack=self.stack.push('additionalProperties'))
            )
            other_schema = (
                other.additional_props
                if isinstance(other.additional_props, MetaModel)
                else MetaModel(stack=other.stack.push('additionalProperties'))
            )
            model.additional_props = self_schema & other_schema or False

        model.items = not_none_or(self.items, other.items, operator.and_)

        # any_of: list[MetaModel] = dc.field(default_factory=list)
        # one_of: list[MetaModel] = dc.field(default_factory=list)
        # all_of: list[MetaModel] = dc.field(default_factory=list)
        for sub_schema in other.all_of or ():
            model_ = model & sub_schema
            if model_ is None:
                break
            model = model_

        # not_: MetaModel | None = None

        return model

    def _properties_and(self, other: MetaModel) -> dict[str, MetaModel]:
        # If any schema has additionalProperties is false, the names in resulting properties are limited to those of that schema

        new_properties_keys = set((self.properties or {}).keys()) | set((other.properties or {}).keys())

        if self.additional_props is False:
            new_properties_keys &= set(self.properties)
        if other.additional_props is False:
            new_properties_keys &= set(other.properties)

        # prepare schemas
        # If both schemas have the same property, their sub-schemas are merged.
        # If one of the schemas doesn't, its additionalProperties schema is merged instead, if present
        new_properties: dict[str, MetaModel] = {}
        for prop_name in new_properties_keys:
            self_schema = (self.properties or {}).get(prop_name)
            other_schema = (other.properties or {}).get(prop_name)
            schema = not_none_or(self_schema, other_schema, operator.and_)
            if schema is None:
                break

            if not self_schema and isinstance(self.additional_props, MetaModel):
                schema &= self.additional_props

            if schema is None:
                break

            if not other_schema and isinstance(other.additional_props, MetaModel):
                schema &= other.additional_props
            if schema is None:
                break

            new_properties[prop_name] = schema

        return new_properties

    def as_type(self, root_package: str) -> python.SchemaClass | None:
        assert self.type_ is not None
        if schema31.DataType.OBJECT not in self.type_:
            return None

        # name = value.lapidary_name or stack.top()
        name = self.stack.top()  # TODO
        fields = [
            model._as_class_field(root_package, name, name in self.props_required)
            for name, model in self.properties.items()
        ]

        # synthetic fields for any_of / one_of

        union_items: Collection[MetaModel] | None = not_none_or(
            self.any_of,
            self.one_of,
            lambda any_of, one_of: list(
                filter(None, [item_any & item_one for item_any, item_one in itertools.product(any_of, one_of)])
            ),
        )

        if union_items:
            fields.append(
                python.AnnotatedVariable(
                    name='model_anyone_of',
                    typ=python.union_of(*(model.as_annotation(root_package) for model in union_items)),
                    required=True,
                    alias=None,
                )
            )

        return python.SchemaClass(
            name=names.maybe_mangle_name(name),
            base_type=ModelBase,
            allow_extra=self.additional_props is not False,
            fields=fields,
            docstr=self.description or None,
        )

    def _as_class_field(self, root_package: str, name: str, required: bool) -> python.AnnotatedVariable:
        python_name = names.maybe_mangle_name(name)
        return python.AnnotatedVariable(
            name=python_name,
            typ=self.as_annotation(root_package, required),
            alias=name if name != python_name else None,
            required=required,
        )

    def as_annotation(
        self, root_package: str, required: bool = True, include_object: bool = True
    ) -> python.AnnotatedType:
        """
        Create type hint for the type represented by the source schema.

        In case where object schema and oneOf or anyOf is used, a type hint for the root schema is created, and the
        items are rendered in as_type as synthetic class fields.

        :param root_package: root python package for object models
        :param required: if false, make the type a Union with None
        :param include_object: if true and the model type includes schema, include the class FQN in the resulting type hint
        """

        union_items = not_none_or(
            self.any_of,
            self.one_of,
            lambda any_of, one_of: list(
                filter(
                    None,
                    [
                        set_multi(self._only_constraints(), item_any, item_one)
                        for item_any, item_one in itertools.product(any_of, one_of)
                    ],
                )
            ),
        )

        types: set[python.AnnotatedType] = set()
        if union_items:
            try:
                types = set(item.as_annotation(root_package, True, False) for item in union_items)
            except TypeError:
                raise
            if include_object:
                if any(schema31.DataType.OBJECT in item.type_ for item in union_items):  # type: ignore[operator]
                    types.add(resolve_type_name(root_package, self.stack))
        else:
            for schema_type in self.type_ or ():
                if include_object is False and schema_type == schema31.DataType.OBJECT:
                    continue

                match schema_type:
                    case schema31.DataType.STRING:
                        try:
                            typ = AnnotatedType(python.GenericType(FORMAT_ENCODERS[(schema_type, self.format)]))
                        except KeyError:
                            typ = python.AnnotatedType.from_type(str)
                    case schema31.DataType.BOOLEAN:
                        typ = python.AnnotatedType.from_type(bool)
                    case schema31.DataType.NUMBER:
                        typ = python.AnnotatedType.from_type(float)
                    case schema31.DataType.INTEGER:
                        typ = python.AnnotatedType.from_type(int)
                    case schema31.DataType.NULL:
                        typ = python.NoneMetaType
                    case schema31.DataType.OBJECT:
                        typ = resolve_type_name(root_package, self.stack)
                    case schema31.DataType.ARRAY:
                        typ = python.list_of(
                            self.items.as_annotation(root_package) if self.items else AnyJsonType,
                        )
                    case _:
                        raise TypeError(schema_type)
                try:
                    types.add(typ)
                except TypeError:
                    raise

        if not required:
            types.add(python.NoneMetaType)

        return python.union_of(*types)


def resolve_type_name(root_package: str, pointer: Stack) -> python.AnnotatedType:
    # FIXME all fields should be saved as json ref; all schemas saved in a map with json ref as a key

    parts = [names.maybe_mangle_name(json_pointer.decode_json_pointer(part)) for part in pointer.path[1:]]
    module_name = '.'.join([root_package, *(part for part in parts[:-1])])
    top = parts[-1]
    return python.AnnotatedType(python.GenericType(python.NameRef(module_name, top)))


FORMAT_ENCODERS = {
    (schema31.DataType.STRING, None): python.NameRef.from_type(str),
    (schema31.DataType.STRING, 'uuid'): python.NameRef(module='uuid', name='UUID'),
    (schema31.DataType.STRING, 'date'): python.NameRef(module='datetime', name='date'),
    (schema31.DataType.STRING, 'date-time'): python.NameRef(module='datetime', name='datetime'),
    (schema31.DataType.STRING, 'time'): python.NameRef(module='datetime', name='time'),
    (schema31.DataType.STRING, 'decimal'): python.NameRef(module='decimal', name='Decimal'),
}


def set_multi(model: MetaModel | None, *models: MetaModel) -> MetaModel | None:
    result = model
    for item in models:
        result = not_none_or(result, item, operator.and_)
    return result
