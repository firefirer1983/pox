from pox.token import Token
import logging
from enum import StrEnum
from typing import Optional, Any
from .statement import Stmt
from .base import PoxCallable, Visitor, RunError, ReturnException
from .environment import Environment


logger = logging.getLogger(__name__)


class FunctionType(StrEnum):
    NONE = "NONE"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    INITIALIZER = "INITIALIZER"


class PoxFunction(PoxCallable):
    def __init__(
        self, stmt: Stmt.Function, env: Environment, initializer: bool = False
    ):
        self.stmt = stmt
        self.closure = env
        self.initializer = initializer

    def arity(self):
        return len(self.stmt.parameters)

    def to_str(self) -> str:
        parameters = ",".join(self.stmt.parameters) or ""
        return f"fun<{self.stmt.name.lexeme}({parameters})>"

    def call(
        self,
        interpreter: Visitor,
        arguments: Optional[list[Any]] = None,
    ) -> Any:
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
            if self.initializer:
                return self.closure.vars["this"]
            return exc.get_value()
        assert False, "Not reachable"

    def bind(self, instance: "PoxInstance") -> "PoxFunction":
        env = Environment(self.closure)
        env.define("this", instance)
        return PoxFunction(self.stmt, env, self.initializer)

    @property
    def block(self) -> Stmt.Block:
        return self.stmt.block

    @property
    def parameters(self) -> list[Token]:
        return self.stmt.parameters


class ClassTye(StrEnum):
    NONE = "NONE"
    CLASS = "CLASSE"
    SUPER = "SUPER"


class PoxClass(PoxCallable):
    def __init__(self, name: Token, methods: list[PoxFunction]):
        self.name = name
        self.methods: dict[str, PoxFunction] = {m.stmt.name.lexeme: m for m in methods}

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
        return f"Class {self.name.lexeme}"


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
