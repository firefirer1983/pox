from typing import Any
from abc import ABC, abstractmethod
from functools import singledispatchmethod

LiteralTypes = bool | str | int | float | None


class ParseError(SyntaxError):
    pass


class RunError(RuntimeError):
    pass


class Visitor(ABC):
    @singledispatchmethod
    @abstractmethod
    def visit(self, expr: "Expression") -> Any:
        raise NotImplementedError()


class Expression(ABC):
    def accept(self, visitor: Visitor):
        return visitor.visit(self)


class Statement(ABC):
    def accept(self, visitor: Visitor):
        return visitor.visit(self)


def literal2str(literal: LiteralTypes) -> str:
    if isinstance(literal, str):
        return literal
    return f"{literal}"
