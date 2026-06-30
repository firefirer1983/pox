from functools import singledispatchmethod
from .token import TokenType
from .expression import Expr
from .statement import Stmt
from .base import Visitor, Expression, Statement, LiteralTypes, ParseError

class AstPrinter(Visitor):
    @singledispatchmethod
    def visit(self, expr: Expression) -> str:
        raise NotImplementedError(type(expr))

    @visit.register
    def _(self, expr: Expr.Binary) -> str:
        return (
            f"({expr.operator.lexeme} {self.visit(expr.left)} {self.visit(expr.right)})"
        )

    @visit.register
    def _(self, expr: Expr.Literal) -> str:
        return f"{expr.value}"

    @visit.register
    def _(self, expr: Expr.Unary) -> str:
        return f"{expr.operator.lexeme}{self.visit(expr.right)}"

    @visit.register
    def _(self, expr: Expr.Grouping) -> str:
        return f"({self.visit(expr.expr)})"


class Interpreter(Visitor):
    @singledispatchmethod
    def visit(self, expr: Expression) -> LiteralTypes:
        raise NotImplementedError(type(expr))

    @visit.register
    def _(self, expr: Expr.Binary) -> LiteralTypes:
        left = self.visit(expr.left)
        right = self.visit(expr.right)
        match expr.operator.token_type:
            case TokenType.GREATER:
                # pyrefly:ignore[unsupported-operation]
                return left > right
            case TokenType.GREATER_EQUAL:
                # pyrefly:ignore[unsupported-operation]
                return left >= right
            case TokenType.LESS:
                # pyrefly:ignore[unsupported-operation]
                return left < right
            case TokenType.LESS_EQUAL:
                # pyrefly:ignore[unsupported-operation]
                return left <= right
            case TokenType.PLUS:
                # pyrefly:ignore[unsupported-operation]
                return left + right
            case TokenType.MINUS:
                # pyrefly:ignore[unsupported-operation]
                return left - right
            case TokenType.STAR:
                # pyrefly:ignore[unsupported-operation]
                return left * right
            case TokenType.SLASH:
                # pyrefly:ignore[unsupported-operation]
                return left / right
            case TokenType.BANG_EQUAL:
                # pyrefly:ignore[unsupported-operation]
                return left != right
            case TokenType.EQUAL_EQUAL:
                # pyrefly:ignore[unsupported-operation]
                return left == right
            case _:
                raise ParseError()

    @visit.register
    def _(self, expr: Expr.Literal) -> LiteralTypes:
        return expr.value

    @visit.register
    def _(self, expr: Expr.Unary) -> LiteralTypes:
        right = self.visit(expr.right)
        if expr.operator.token_type == TokenType.MINUS:
            if not isinstance(right, (float, int)):
                raise ParseError()
            return -1 * right
        elif expr.operator.token_type == TokenType.BANG:
            return bool(right)
        raise ParseError()

    @visit.register
    def _(self, expr: Expr.Grouping) -> LiteralTypes:
        return self.visit(expr.expr)
