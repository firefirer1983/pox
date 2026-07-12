from typing import Any
from abc import ABC, abstractmethod
from functools import singledispatchmethod


class PoxCallable:
    @abstractmethod
    def arity(self) -> int: ...

    @abstractmethod
    def to_str(self) -> str: ...


LiteralTypes = bool | str | int | float | None | PoxCallable


class ParseError(SyntaxError):
    pass


class RunError(RuntimeError):
    pass


class ReturnException(RuntimeError):
    def __init__(self, value: LiteralTypes):
        self.value = value

    def get_value(self):
        return self.value

class Expression(ABC):
    def accept(self, visitor: "Visitor"):
        return visitor.visit(self)


class Statement(ABC):
    def accept(self, visitor: "Visitor"):
        return visitor.visit(self)


class Visitor(ABC):
    @singledispatchmethod
    @abstractmethod
    def visit(self, stmt: Statement | Expression) -> Any:
        raise NotImplementedError()


def literal2str(literal: LiteralTypes) -> str:
    if isinstance(literal, str):
        return literal
    return f"{literal}"


def is_true(literal: LiteralTypes) -> bool:
    return bool(literal)
