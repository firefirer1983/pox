from typing import Any
from abc import ABC, abstractmethod
from functools import singledispatchmethod

LiteralTypes = bool | str | int | float | None


class ParseError(SyntaxError):
    pass


class RunError(RuntimeError):
    pass



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
