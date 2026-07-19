from pox.base import PoxCallable
from typing import Optional
from .base import Statement, Expression
from .token import Token


class PrintStmt(Statement):
    def __init__(self, expr: Expression):
        self.expr = expr


class ExprStmt(Statement):
    def __init__(self, expr: Expression):
        self.expr = expr


class Var(Statement):
    def __init__(self, name: Token, initilaizer: Optional[Expression] = None):
        self.name = name
        self.initializer = initilaizer


class Block(Statement):
    def __init__(self, statements: list[Statement]):
        self.statements = statements


class IF(Statement):
    def __init__(
        self,
        condition: Expression,
        consequent: Statement,
        alternative: Optional[Statement] = None,
    ):
        self.condition = condition
        self.consequent = consequent
        self.alternative = alternative


class While(Statement):
    def __init__(self, condition: Expression, statement: Statement):
        self.condition = condition
        self.statement = statement


class Function(Statement):
    def __init__(self, name: str, arguments: list[str], block: Block):
        self.name = name
        self.parameters = arguments[:]
        self.block = block


class Return(Statement):
    def __init__(self, expr: Expression):
        self.value = expr


class Class(Statement):
    def __init__(self, name: str, methods: list[Function]):
        self.name = name
        self.methods = methods[:]


class Stmt:
    PrintStmt = PrintStmt
    ExprStmt = ExprStmt
    Var = Var
    Block = Block
    IF = IF
    While = While
    Function = Function
    Return = Return
    Class = Class
