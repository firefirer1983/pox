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


class Stmt:
    PrintStmt = PrintStmt
    ExprStmt = ExprStmt
    Var = Var
