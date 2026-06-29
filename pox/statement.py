from .base import Statement, Expression, Visitor


class PrintStmt(Statement):
    def __init__(self, expr: Expression):
        self.expr = expr

    def accept(self, visitor: Visitor):
        return visitor.visit(self)


class ExprStmt(Statement):
    def accept(self, visitor: Visitor):
        return visitor.visit(self)


class Stmt:
    PrintStmt = PrintStmt
    ExprStmt = ExprStmt
