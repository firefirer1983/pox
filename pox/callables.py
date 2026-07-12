from typing import Any, cast
from abc import abstractmethod
from .statement import Statement, Stmt
from .expression import Expr
from .environment import Environment
from .base import Visitor, LiteralTypes, PoxCallable

        
class PoxFunction(PoxCallable):
    def __init__(self, stmt: Stmt.Function):
        self.stmt = stmt

    def arity(self):
        return len(self.stmt.parameters)

    @property
    def block(self) -> Stmt.Block:
        return self.stmt.block

    @property
    def parameters(self)-> list[str]:
        return self.stmt.parameters
