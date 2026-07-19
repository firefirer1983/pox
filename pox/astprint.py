import logging
from ast import literal_eval
from functools import singledispatchmethod
from .base import Statement, LiteralTypes, RunError
from .token import TokenType


from .expression import Expr
from .statement import Stmt
from .base import (
    Visitor,
    Expression,
)

logger = logging.getLogger(__name__)


class AstPrinter(Visitor):
    @singledispatchmethod
    def visit(self, expr: Expression | Statement) -> str:
        raise NotImplementedError(type(expr))

    def eval(self, value: str) -> str:
        logger.info(f"eval({value})")
        try:
            return str(literal_eval(value))
        except ValueError:
            return value

    @visit.register
    def _(self, expr: Expr.Binary) -> str:
        return (
            f"({self.visit(expr.left)}{expr.operator.lexeme}{self.visit(expr.right)})"
        )

    @visit.register
    def _(self, expr: Expr.Literal) -> str:
        return self.eval(str(expr.value))

    @visit.register
    def _(self, expr: Expr.Unary) -> str:
        right = self.visit(expr.right)
        match expr.operator.token_type:
            case TokenType.MINUS:
                result = -1 * literal_eval(right)
            case TokenType.PLUS:
                result = self.visit(right)
            case TokenType.BANG:
                result = not literal_eval(right)
            case _:
                RunError(f"Syntax error: {expr.operator.lexeme}{right}")
        return str(result)

    @visit.register
    def _(self, expr: Expr.Grouping) -> str:
        return f"({self.visit(expr.expr)})"

    @visit.register
    def _(self, expr: Expr.Variable) -> str:
        return f"{expr.identify.lexeme}"

    @visit.register
    def _(self, expr: Expr.Assign) -> str:
        return f"{expr.identify.lexeme}={self.visit(expr.value)}"

    @visit.register
    def _(self, stmt: Stmt.Var) -> str:
        value = ""
        result = f"var {stmt.name.lexeme}"
        if stmt.initializer:
            value = self.visit(stmt.initializer)
            result += f"={value}"
        result += ";"
        return result

    @visit.register
    def _(self, stmt: Stmt.Block) -> str:
        result = "{"
        for statement in stmt.statements:
            result += self.visit(statement)
        result += "}"
        return result

    @visit.register
    def _(self, stmt: Stmt.ExprStmt) -> str:
        return f"{self.visit(stmt.expr)};"

    @visit.register
    def _(self, stmt: Stmt.IF) -> str:
        result = f"if ({self.visit(stmt.condition)})"
        result += self.visit(stmt.consequent)
        if stmt.alternative:
            result += self.visit(stmt.alternative)
        return result

    @visit.register
    def _(self, expr: Expr.Logical) -> str:
        return (
            f"({self.visit(expr.left)} {expr.operator.lexeme} {self.visit(expr.right)})"
        )

    @visit.register
    def _(self, stmt: Stmt.While) -> str:
        return f"while({self.visit(stmt.condition)}){self.visit(stmt.statement)}"

    @visit.register
    def _(self, expr: Expr.Call) -> str:
        result = f"{self.visit(expr.expr)}("
        for i, arg in enumerate(expr.arguments):
            result += f"{self.visit(arg)}"
            if i + 1 == len(expr.arguments):
                break
            result += ","
        return result

    @visit.register
    def _(self, stmt: Stmt.Function) -> str:
        result = f"fun {stmt.name}({','.join(stmt.parameters)})"
        result += f"{self.visit(stmt.block)}"
        return result

    @visit.register
    def _(self, stmt: Stmt.Return) -> str:
        return f"return {self.visit(stmt.value)};"
