from typing import Any, Optional
from enum import StrEnum
from .callables import PoxFunction
from .base import RunError, PoxCallable, Visitor


class ClassTye(StrEnum):
    NONE = "NONE"
    CLASS = "CLASSE"
    SUPER = "SUPER"


class PoxClass(PoxCallable):
    def __init__(self, name: str, methods: list[PoxFunction]):
        self.name = name
        self.methods: dict[str, PoxFunction] = {m.stmt.name: m for m in methods}

    def find_method(self, name: str) -> None | PoxFunction:
        return self.methods.get(name)

    def call(self, interpreter: Visitor, arguments: Optional[list[Any]] = None):
        instance = PoxInstance(self)
        initializer = self.find_method("init")
        if initializer:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    def arity(self):
        init_func = self.find_method("init")
        if not init_func:
            return 0
        return init_func.arity()

    def to_str(self):
        return f"Class {self.name}"


class PoxInstance:
    def __init__(self, klass: PoxClass):
        self.fields: dict[str, Any] = dict()
        self.klass = klass

    def get(self, name: str):
        if name in self.fields:
            return self.fields[name]

        method = self.klass.find_method(name)
        if not method:
            raise RunError(f"Missing method {name} in class {self.klass.name}")
        return method.bind(self)

    def set(self, name: str, value: Any):
        self.fields[name] = value
