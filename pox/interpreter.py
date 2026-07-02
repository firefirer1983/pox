from pox.environment import global_env
import logging
import logging
import sys
from functools import singledispatchmethod
from .token import TokenType
from .environment import Environment
from .expression import Expr
from .statement import Stmt
from .base import Visitor, Expression, LiteralTypes, ParseError, literal2str, is_true


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
        result = "{\n"
        for statement in stmt.statements:
            result += "\t"
            result += self.visit(statement)
            result += "\n"
        result += "}"
        return result

    @visit.register
    def _(self, stmt: Stmt.ExprStmt) -> str:
        return f"{self.visit(stmt.expr)};"

    @visit.register
    def _(self, stmt: Stmt.IF) -> str:
        result = f"if ({self.visit(stmt.condition)})"
        result += "\n"
        result += self.visit(stmt.consequent)
        if stmt.alternative:
            result += "\n"
            result += self.visit(stmt.alternative)
        return result

    @visit.register
    def _(self, expr: Expr.Logical) -> str:
        return (
            f"({expr.operator.lexeme} {self.visit(expr.left)} {self.visit(expr.right)})"
        )


class Interpreter(Visitor):
    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    @singledispatchmethod
    def visit(self, expr: Expression, env: Environment) -> LiteralTypes:
        raise NotImplementedError(type(expr))

    @visit.register
    def _(self, expr: Expr.Binary, env: Environment = global_env) -> LiteralTypes:
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
    def _(self, expr: Expr.Literal, env: Environment = global_env) -> LiteralTypes:
        return expr.value

    @visit.register
    def _(self, expr: Expr.Unary, env: Environment = global_env) -> LiteralTypes:
        right = self.visit(expr.right)
        if expr.operator.token_type == TokenType.MINUS:
            if not isinstance(right, (float, int)):
                raise ParseError()
            return -1 * right
        elif expr.operator.token_type == TokenType.BANG:
            return bool(right)
        raise ParseError()

    @visit.register
    def _(self, expr: Expr.Grouping, env: Environment = global_env) -> LiteralTypes:
        return expr.expr.accept(self)

    @visit.register
    def _(self, expr: Expr.Variable, env: Environment = global_env) -> LiteralTypes:
        return env.get(expr.identify.lexeme)

    @visit.register
    def _(self, expr: Expr.Assign, env: Environment = global_env) -> LiteralTypes:
        env.assign(expr.identify.lexeme, self.visit(expr.value))

    @visit.register
    def _(self, stmt: Stmt.PrintStmt, env: Environment = global_env):
        string = literal2str(self.visit(stmt.expr))
        sys.stdout.write(string)
        sys.stdout.flush()

    @visit.register
    def _(self, stmt: Stmt.ExprStmt, env: Environment = global_env):
        return self.visit(stmt.expr, env)

    @visit.register
    def _(self, stmt: Stmt.Var, env: Environment = global_env):
        value = None
        if stmt.initializer:
            value = self.visit(stmt.initializer, env)
        env.define(stmt.name.lexeme, value)

    @visit.register
    def _(self, stmt: Stmt.Block, env: Environment = global_env):
        env = Environment(env)
        for statement in stmt.statements:
            self.visit(statement, env)

    @visit.register
    def _(self, stmt: Stmt.IF):
        if is_true(self.visit(stmt.condition)):
            self.visit(stmt.consequent)
        elif stmt.alternative:
            self.visit(stmt.alternative)
