from __future__ import annotations

import importlib

from pydantic import BaseModel, Extra


class TypeHint(BaseModel):
    module: str
    name: str

    class Config:
        extra = Extra.forbid

    def __repr__(self):
        return self.full_name()

    def full_name(self):
        return self.module + '.' + self.name if self.module != 'builtins' else self.name

    @staticmethod
    def from_str(path: str) -> TypeHint:
        module, name = path.split(':')
        return TypeHint(module=module, name=name)

    @staticmethod
    def from_type(typ: type) -> TypeHint:
        if hasattr(typ, '__origin__'):
            raise ValueError('Generic types unsupported', typ)
        module = typ.__module__
        name = typ.__name__
        if module == 'builtins':
            return BuiltinTypeHint.from_str(name)
        else:
            return TypeHint(module=module, name=name)

    def imports(self) -> list[str]:
        return [self.module]

    def union_with(self, other: TypeHint) -> GenericTypeHint:
        return GenericTypeHint(module='typing', name='Union', args=[self, other])

    def list_of(self) -> GenericTypeHint:
        return GenericTypeHint(module='builtins', name='list', args=[self])

    def _types(self) -> list[TypeHint]:
        return [self]

    def __eq__(self, other) -> bool:
        return (
                isinstance(other, TypeHint)
                # generic type hint has args, so either both should be generic or none
                and isinstance(self, GenericTypeHint) == isinstance(other, GenericTypeHint)
                and self.module == other.module
                and self.name == other.name
        )

    def __hash__(self) -> int:
        return self.module.__hash__() * 14159 + self.name.__hash__()

    def resolve(self) -> type:
        mod = importlib.import_module(self.module)
        return getattr(mod, self.name)


class BuiltinTypeHint(TypeHint):
    module: str = 'builtins'

    class Config:
        extra = Extra.forbid

    def __repr__(self):
        return self.full_name()

    @staticmethod
    def from_str(name: str) -> BuiltinTypeHint:
        return BuiltinTypeHint(name=name)

    def imports(self) -> list[str]:
        return []

    def full_name(self):
        return self.name


class GenericTypeHint(TypeHint):
    args: tuple[TypeHint, ...]

    class Config:
        extra = Extra.forbid

    def union_with(self, other: TypeHint) -> GenericTypeHint:
        if self.module == 'typing' and self.name == 'Union':
            return GenericTypeHint(module=self.module, name=self.name, args=[*self.args, other])
        else:
            return super().union_with(other)

    @staticmethod
    def union_of(types: tuple[TypeHint, ...]) -> GenericTypeHint:
        args = set()
        for typ in types:
            if isinstance(typ, GenericTypeHint) and typ.module == 'typing' and typ.name == 'Union':
                args.update(typ.args)
            else:
                args.add(typ)
        return GenericTypeHint(module='typing', name='Union', args=sorted(args, key=lambda t: str(t)))

    def imports(self) -> list[str]:
        return [
            imp
            for typ in self._types()
            for imp in TypeHint.imports(typ)
            if imp != 'builtins'
        ]

    def _types(self) -> list[TypeHint]:
        return [self, *[typ for arg in self.args for typ in arg._types()]]

    def resolve(self) -> type:
        generic = super().resolve()
        return generic[tuple(arg.resolve() for arg in self.args)]

    def __repr__(self) -> str:
        return self.full_name()

    def full_name(self) -> str:
        return f'{super().full_name()}[{", ".join(arg.full_name() for arg in self.args)}]'

    @property
    def origin(self) -> TypeHint:
        return TypeHint(module=self.module, name=self.name)

    def __eq__(self, other) -> bool:
        return (
                isinstance(other, GenericTypeHint)
                and self.module == other.module
                and self.name == other.name
                and self.args == other.args
        )

    def __hash__(self) -> int:
        hash_ = super().__hash__()
        for arg in self.args:
            hash_ = (hash_ << 1) + arg.__hash__()
        return hash_
