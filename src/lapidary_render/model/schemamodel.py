from __future__ import annotations

import dataclasses as dc
import itertools
import operator
import types
from collections.abc import Callable, Container, Iterable, Set
from typing import Any, Self

from openapi_pydantic.v3.v3_1 import schema as schema31
from pydantic.alias_generators import to_pascal

from . import stack as stack_

JSON_TYPE_TO_PY_TYPE: dict[schema31.DataType, type] = {
    schema31.DataType.ARRAY: list,
    schema31.DataType.BOOLEAN: bool,
    schema31.DataType.INTEGER: int,
    schema31.DataType.NULL: types.NoneType,
    schema31.DataType.NUMBER: float,
    schema31.DataType.OBJECT: dict,
    schema31.DataType.STRING: str,
}

PY_TYPE_TO_JSON_TYPE: dict[type, schema31.DataType] = {value: key for key, value in JSON_TYPE_TO_PY_TYPE.items()}


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


def _all_types() -> set[schema31.DataType]:
    return {typ for typ in schema31.DataType}


def diff_dicts(dict1, dict2):
    # Keys unique to dict1
    unique_to_dict1 = {key: dict1[key] for key in dict1 if key not in dict2 or dict1[key] != dict2[key]}

    # Keys unique to dict2
    unique_to_dict2 = {key: dict2[key] for key in dict2 if key not in dict1 or dict1[key] != dict2[key]}

    return unique_to_dict1, unique_to_dict2


@dc.dataclass(kw_only=True)
class SchemaModel:
    """
    Here we decide whether a schema transforms into a type annotation, class or both.
    It's a class when schemas is object type, type annotation when it's non-object type, and both when it's both object and non-object.
    """

    # used to generate package, module and class name
    stack: stack_.Stack

    title: str | None = None
    description: str | None = None

    type_: set[schema31.DataType] | None = None
    enum: set[Any] | None = None

    # if not required, join the python type in union with None and add default value None
    required: bool = True
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

    properties: dict[str, SchemaModel] = dc.field(default_factory=dict)
    additional_props: SchemaModel | bool = True
    props_required: Set[str] = dc.field(default_factory=set)

    items: SchemaModel | None = None

    any_of: list[SchemaModel] | None = None
    one_of: list[SchemaModel] | None = None
    all_of: list[SchemaModel] | None = None

    def normalize_model(self) -> SchemaModel | None:
        if self.type_ is None:
            self.type_ = _all_types()

        # limit types and enum values to intersection of types
        if self.enum is not None:
            enum_types = {PY_TYPE_TO_JSON_TYPE[type(v)] for v in self.enum}
            self.type_ = self.type_ & enum_types
            if not self.type_:
                return None
            allowed_py_types = tuple(JSON_TYPE_TO_PY_TYPE[t] for t in self.type_)
            self.enum = {v for v in self.enum if isinstance(v, allowed_py_types)}

        # promote single-item anyOf/oneOf to allOf so the merge loop handles them
        for attr in ('any_of', 'one_of'):
            items = getattr(self, attr)
            if items and len(items) == 1:
                self.all_of = [*(self.all_of or ()), items[0]]
                setattr(self, attr, None)

        if self.all_of and len(self.all_of) == 1 and not self.has_annotations(excluding=('all_of',)):
            return self.all_of[0].normalize_model()

        # merge allOf
        model: SchemaModel | None = self
        for schema in self.all_of or ():
            if model is None:
                return None
            model &= schema.normalize_model()

        assert model is not None
        model.all_of = None

        # push annotations down to anyOf and oneOf
        model_no_any = dc.replace(model, any_of=None, one_of=None)
        for sub_name, subc in (('any_of', model.any_of), ('one_of', model.one_of)):
            if not subc:
                continue
            items = []
            for idx, sub in enumerate(subc):
                nsub = model_no_any.intersect(
                    sub, stack_.Stack((*model.stack.path[:-1], f'{to_pascal(sub_name)}{idx}'))
                )
                if nsub is None:
                    # ignore bottom types
                    continue
                if sub._comparable() == nsub._comparable():
                    # no change
                    nsub = sub
                items.append(nsub)
            setattr(model, sub_name, items)

        # merge oneOf with anyOf
        # not strictly correct, but oneOf is rarely used in the proper way and doing it simplifies the output model
        if self.one_of:
            if self.any_of:
                self.any_of = list(
                    filter(
                        None,
                        [
                            a.intersect(b, stack_.Stack((*model.stack.path[:-1], f'AnyOneOf{idx}')))
                            for idx, (a, b) in enumerate(itertools.product(self.any_of, self.one_of))
                        ],
                    )
                )
            else:
                self.any_of = self.one_of
            self.one_of = None

        return model

    def _only_constraints(self) -> Self:
        return dc.replace(
            self,
            any_of=None,
            all_of=None,
            one_of=None,
        )

    def __and__(self, other) -> SchemaModel | None:
        if not isinstance(other, SchemaModel | bool):
            return NotImplemented
        return self.intersect(other, self.stack)

    def intersect(self, other: SchemaModel | bool, s: stack_.Stack) -> SchemaModel | None:
        if other is None or other is False:
            return None
        if other is True:
            return self
        assert isinstance(other, SchemaModel)

        model = dc.replace(self, stack=s)

        model.type_ = not_none_or(self.type_, other.type_, operator.and_)
        model.enum = not_none_or(self.enum, other.enum, operator.and_)
        model.gt = not_none_or(self.gt, other.gt, max)
        model.ge = not_none_or(self.ge, other.ge, max)
        model.lt = not_none_or(self.lt, other.lt, min)
        model.le = not_none_or(self.le, other.le, min)

        if isinstance(self.multiple_of, float) and isinstance(other.multiple_of, float):
            raise NotImplementedError
        model.multiple_of = self.multiple_of or other.multiple_of

        model.min_length = not_none_or(self.min_length, other.min_length, max)
        model.max_length = not_none_or(self.max_length, other.max_length, min)
        model.pattern = not_none_or(self.pattern, other.pattern, same_or_raise('pattern'))
        model.format = not_none_or(self.format, other.format, same_or_raise('format'))

        model.properties = self._properties_and(other)
        model.props_required = self.props_required | other.props_required

        if isinstance(self.additional_props, bool) and isinstance(other.additional_props, bool):
            model.additional_props = self.additional_props and other.additional_props
        else:
            self_schema = (
                self.additional_props
                if isinstance(self.additional_props, SchemaModel)
                else SchemaModel(stack=self.stack.push('additionalProperties'))
            )
            other_schema = (
                other.additional_props
                if isinstance(other.additional_props, SchemaModel)
                else SchemaModel(stack=other.stack.push('additionalProperties'))
            )
            model.additional_props = self_schema & other_schema or False

        # determine s (resulting class name) based on the presence of properties in both models

        model.items = not_none_or(self.items, other.items, operator.and_)

        for field in ('all_of', 'any_of', 'one_of'):
            merge(model, other, field, operator.add)

        # not_: SchemaModel | None = None

        return model

    def _properties_and(self, other: SchemaModel) -> dict[str, SchemaModel]:
        # If any schema has additionalProperties is false, the names in resulting properties are limited to those of that schema

        new_properties_keys = set((self.properties or {}).keys()) | set((other.properties or {}).keys())

        if self.additional_props is False:
            new_properties_keys &= set(self.properties)
        if other.additional_props is False:
            new_properties_keys &= set(other.properties)

        # prepare schemas
        # If both schemas have the same property, their sub-schemas are merged.
        # If one of the schemas doesn't, its additionalProperties schema is merged instead, if present
        new_properties: dict[str, SchemaModel] = {}
        for prop_name in new_properties_keys:
            self_schema = (self.properties or {}).get(prop_name)
            other_schema = (other.properties or {}).get(prop_name)
            schema = not_none_or(self_schema, other_schema, operator.and_)
            if schema is None:
                break

            if not self_schema and isinstance(self.additional_props, SchemaModel):
                schema &= self.additional_props

            if schema is None:
                break

            if not other_schema and isinstance(other.additional_props, SchemaModel):
                schema &= other.additional_props
            if schema is None:
                break

            new_properties[prop_name] = schema

        return new_properties

    def is_any_obj(self) -> bool:
        """True when this schema describes object without any properties or additional properties."""
        assert self.type_ is not None
        return (
            schema31.DataType.OBJECT in self.type_
            and not self.properties
            and self.additional_props is True
            and all(not sub.properties and sub.additional_props is True for sub in (self.any_of or ()))
            and all(not sub.properties and sub.additional_props is True for sub in (self.one_of or ()))
        )

    def dependencies(self) -> Iterable[SchemaModel]:
        yield from self.any_of or ()
        if self.items is not None:
            yield self.items
        for sub in (self.properties or {}).values():
            yield sub
            yield from sub.dependencies()

        # TODO support additional properties
        # if self.additional_props:
        #     yield self.additional_props

    def has_annotations(self, excluding: Container[str] = ()) -> bool:
        return (
            any(
                getattr(self, key) is not None
                for key in (
                    'enum',
                    'gt',
                    'ge',
                    'lt',
                    'le',
                    'multiple_of',
                    'max_length',
                    'min_length',
                    'pattern',
                    'format',
                    'items',
                    'any_of',
                    'one_of',
                    'all_of',
                )
                if key not in excluding
            )
            or self.additional_props is not True
            or bool(self.properties)
            or bool(self.props_required)
            or self.type_ != _all_types()
        )

    def _comparable(self) -> Self:
        """Return a copy without anotations, useful for comparing."""
        return dc.replace(self, description=None, title=None, stack=stack_.Stack())


def set_multi(model: SchemaModel | None, *models: SchemaModel) -> SchemaModel | None:
    result = model
    for item in models:
        result = not_none_or(result, item, operator.and_)
    return result


def set_intersection[T](a: Set[T] | bool, b: Set[T] | bool) -> Set[T] | bool:
    """
    Variant of set intersection that considers True to mean a set with all possible elements and False an empty set.
    """

    if a is False or b is False:
        return False
    if a is True:
        return b
    if b is True:
        return a
    return a & b


def merge(a, b, key: str, op: Callable) -> None:
    val = not_none_or(getattr(a, key), getattr(b, key), op)
    setattr(a, key, val)
