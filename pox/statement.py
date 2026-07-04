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
    def __init__(self, condition: Expression, consequent: Statement, alternative: Optional[Statement] = None):
        self.condition = condition
        self.consequent = consequent
        self.alternative = alternative

class While(Statement):
    def __init__(self, condition: Expression, body: Block):
        self.condition = condition
        self.body = body

class Stmt:
    PrintStmt = PrintStmt
    ExprStmt = ExprStmt
    Var = Var
    Block = Block
    IF = IF
    While = While
