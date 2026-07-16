import logging
from enum import StrEnum
from typing import Optional
from .statement import Stmt
from .base import PoxCallable, Visitor, LiteralTypes, RunError, ReturnException
from .environment import Environment

logger = logging.getLogger(__name__)


class FunctionType(StrEnum):
    NONE = "NONE"
    FUNCTION = "FUNCTION"


class PoxFunction(PoxCallable):
    def __init__(self, stmt: Stmt.Function, env: Environment):
        self.stmt = stmt
        self.closure = env

    def arity(self):
        return len(self.stmt.parameters)

    def to_str(self) -> str:
        parameters = ",".join(self.stmt.parameters) or ""
        return f"fun<{self.stmt.name}({parameters})>"

    def call(
        self,
        interpreter: Visitor,
        arguments: Optional[list[LiteralTypes]] = None,
    ) -> LiteralTypes:
        arguments = arguments or []
        # 调用的时候从闭包生成新的env，不然多个函数多次调用会打架
        env = Environment(self.closure)
        if len(arguments) != self.arity():
            raise RunError(f"实参数目:{len(arguments)} != 形参数目:{self.arity()}")

        for name, value in zip(self.parameters, arguments):
            env.define(name, value)

        try:
            interpreter.visit(self.block, env)
        except ReturnException as exc:
            return exc.get_value()

    @property
    def block(self) -> Stmt.Block:
        return self.stmt.block

    @property
    def parameters(self) -> list[str]:
        return self.stmt.parameters
