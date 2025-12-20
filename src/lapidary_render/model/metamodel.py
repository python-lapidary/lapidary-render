from __future__ import annotations

import dataclasses as dc
import itertools
import operator
from collections.abc import Callable, Container, Iterable, Set
from typing import Any, Self

from openapi_pydantic.v3.v3_1 import schema as schema31
from pydantic.alias_generators import to_pascal

from .. import json_pointer, names, runtime
from . import python
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


def _all_types() -> set[schema31.DataType]:
    return {typ for typ in schema31.DataType if typ is not schema31.DataType.NULL}


def diff_dicts(dict1, dict2):
    # Keys unique to dict1
    unique_to_dict1 = {key: dict1[key] for key in dict1 if key not in dict2 or dict1[key] != dict2[key]}

    # Keys unique to dict2
    unique_to_dict2 = {key: dict2[key] for key in dict2 if key not in dict1 or dict1[key] != dict2[key]}

    return unique_to_dict1, unique_to_dict2


@dc.dataclass(kw_only=True)
class MetaModel:
    """
    Here we decide whether a schema transforms into a type annotation, class or both.
    It's a class when schemas is object type, type annotation when it's non-object type, and both when it's both object and non-object.
    """

    # used to generate package, module and class name
    stack: Stack

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

    properties: dict[str, MetaModel] = dc.field(default_factory=dict)
    additional_props: MetaModel | bool = True
    props_required: Set[str] = dc.field(default_factory=set)

    items: MetaModel | None = None

    any_of: list[MetaModel] | None = None
    one_of: list[MetaModel] | None = None
    all_of: list[MetaModel] | None = None

    def normalize_model(self) -> MetaModel | None:
        # if this doesn't have any assertions and only a single sub-schema, return that sub-schema
        if len(self.any_of or ()) + len(self.one_of or ()) + len(self.all_of or ()) == 1:
            if self.any_of:
                candidate = self.any_of[0]
            elif self.one_of:
                candidate = self.one_of[0]
            elif self.all_of:
                candidate = self.all_of[0]
            else:
                raise ValueError

            if self._only_constraints() == MetaModel(stack=self.stack) or self._only_constraints() == MetaModel(
                stack=self.stack, type_=candidate.type_
            ):
                return candidate

        if self.type_ is None:
            self.type_ = _all_types()

        # merge allOf
        model: MetaModel | None = self
        for schema in self.all_of or ():
            if model is None:
                return None
            model &= schema

        assert model is not None
        model.all_of = None

        # push annotations down to anyOf and oneOf
        model_no_any = dc.replace(model, any_of=None, one_of=None)
        for sub_name, subc in (('any_of', model.any_of), ('one_of', model.one_of)):
            if not subc:
                continue
            items = []
            for idx, sub in enumerate(subc):
                nsub = model_no_any.intersect(sub, Stack((*model.stack.path[:-1], f'{to_pascal(sub_name)}{idx}')))
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
                            a.intersect(b, Stack((*model.stack.path[:-1], f'AnyOneOf{idx}')))
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

    def __and__(self, other) -> MetaModel | None:
        if not isinstance(other, MetaModel | bool):
            return NotImplemented
        return self.intersect(other, self.stack)

    def intersect(self, other: MetaModel | bool, stack: Stack) -> MetaModel | None:
        if other is None or other is False:
            return None
        if other is True:
            return self
        assert isinstance(other, MetaModel)

        model = dc.replace(self, stack=stack)

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
                if isinstance(self.additional_props, MetaModel)
                else MetaModel(stack=self.stack.push('additionalProperties'))
            )
            other_schema = (
                other.additional_props
                if isinstance(other.additional_props, MetaModel)
                else MetaModel(stack=other.stack.push('additionalProperties'))
            )
            model.additional_props = self_schema & other_schema or False

        # determine stack (resulting class name) based on the presence of properties in both models

        model.items = not_none_or(self.items, other.items, operator.and_)

        for field in ('all_of', 'any_of', 'one_of'):
            merge(model, other, field, operator.and_)

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

    def _is_any_obj(self) -> bool:
        """True when this schema describes object without any properties or additional properties."""
        assert self.type_ is not None
        return (
            schema31.DataType.OBJECT in self.type_
            and not self.properties
            and self.additional_props is True
            and all(not sub.properties and sub.additional_props is True for sub in (self.any_of or ()))
            and all(not sub.properties and sub.additional_props is True for sub in (self.one_of or ()))
        )

    def _as_type(self, package: str) -> python.SchemaClass | None:
        """convert current schema model, excluding any sub-schemas"""
        # name = value.lapidary_name or stack.top()
        name = self.stack.top()  # TODO
        fields = [
            _as_class_field(
                model.as_annotation(package, name in self.props_required), name, name in self.props_required
            )
            for name, model in self.properties.items()
        ]

        return python.SchemaClass(
            name=names.maybe_mangle_name(name),
            base_type=runtime.ModelBase,
            allow_extra=self.additional_props is not False,
            fields=fields,
            docstr=self.description or None,
        )

    def as_type(self, root_package: str) -> python.SchemaClass | None:
        if not self.any_of and self.type_ and schema31.DataType.OBJECT in self.type_ and not self._is_any_obj():
            return self._as_type(root_package)  # type: ignore[misc]
        return None

    def dependencies(self) -> Iterable[MetaModel]:
        yield from self.any_of or ()
        if self.items is not None:
            yield self.items
        for sub in (self.properties or {}).values():
            yield sub
            yield from sub.dependencies()

        # TODO support additional properties
        # if self.additional_props:
        #     yield self.additional_props

    def as_annotation(
        self, root_package: str, required: bool = True, include_object: bool = True
    ) -> python.AnnotatedType:
        """
        Create type hint for the type represented by the source schema.

        In case where object schema with oneOf or anyOf is used, a type hint for the parent schema is created, and the
        items are rendered in as_type() as a synthetic class field.

        :param root_package: root python package for object models
        :param required: if false, make the type a Union with None
        :param include_object: if true and the model type includes schema, include the class FQN in the resulting type hint
        """

        if not self._has_annotations():
            return runtime.JsonValue

        if self.any_of:
            return python.union_of(*[t.as_annotation(root_package, required) for t in self.any_of])

        else:
            types: set[python.AnnotatedType] = set()
            for schema_type in self.type_ or ():
                if include_object is False and schema_type == schema31.DataType.OBJECT:
                    continue

                match schema_type:
                    case schema31.DataType.STRING:
                        try:
                            typ = python.AnnotatedType(FORMAT_ENCODERS[(schema_type, self.format)])  # type: ignore[index]
                        except KeyError:
                            typ = self._as_str_anno()
                    case schema31.DataType.BOOLEAN:
                        typ = python.AnnotatedType.from_type(bool)
                    case schema31.DataType.NUMBER:
                        typ = self._as_numeric_anno(float)
                    case schema31.DataType.INTEGER:
                        typ = self._as_numeric_anno(int)
                    case schema31.DataType.NULL:
                        typ = python.NoneMetaType
                    case schema31.DataType.OBJECT:
                        typ = self._as_object_anno(root_package)
                    case schema31.DataType.ARRAY:
                        typ = python.list_of(
                            self.items.as_annotation(root_package) if self.items else runtime.JsonValue,
                        )
                    case _:
                        raise TypeError(schema_type)
                types.add(typ)

        if not required:
            types.add(python.NoneMetaType)

        return python.union_of(*types)

    def _as_numeric_anno(self, typ: type) -> python.AnnotatedType:
        num_constraints = {'lt', 'gt', 'ge', 'le', 'multiple_of'}
        constraints = {}
        for key in num_constraints:
            if (value := getattr(self, key)) is not None:
                constraints[key] = typ(value)
        return python.AnnotatedType(
            python.NameRef.from_type(typ),
            **constraints,  # type: ignore[arg-type]
        )

    def _as_str_anno(self) -> python.AnnotatedType:
        str_constraints = {'max_length', 'min_length', 'pattern'}
        constraints = {key: value for key in str_constraints if (value := getattr(self, key)) is not None}
        return python.AnnotatedType(
            python.NameRef('builtins', 'str'),
            **constraints,  # type: ignore[arg-type]
        )

    def _as_object_anno(self, root_package: str) -> python.AnnotatedType:
        if not self.properties and not (
            any(sub.properties for sub in self.any_of or () if schema31.DataType.OBJECT in (sub.type_ or ()))
            and any(sub.properties for sub in self.one_of or () if schema31.DataType.OBJECT in (sub.type_ or ()))
        ):
            return runtime.JsonObject
        else:
            return resolve_type_name(root_package, self.stack)

    def _has_annotations(self, excluding: Container[str] = ()) -> bool:
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
        return dc.replace(self, description=None, title=None, stack=Stack())


def _as_class_field(anno: python.AnnotatedType, name: str, required: bool) -> python.AnnotatedVariable:
    python_name = names.maybe_mangle_name(name)
    return python.AnnotatedVariable(
        name=python_name,
        typ=anno,
        alias=name if name != python_name else None,
        required=required,
    )


def resolve_type_name(root_package: str, pointer: Stack) -> python.AnnotatedType:
    # FIXME all fields should be saved as json ref; all schemas saved in a map with json ref as a key

    parts = [names.maybe_mangle_name(json_pointer.decode_json_pointer(part)) for part in pointer.path[1:]]
    module_name = '.'.join([root_package, *(part for part in parts[:-1])])
    top = parts[-1]
    return python.AnnotatedType(python.NameRef(module_name, top))


FORMAT_ENCODERS = {
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
