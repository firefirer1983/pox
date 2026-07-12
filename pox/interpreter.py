import sys
import logging
from typing import cast

from functools import singledispatchmethod
from .token import TokenType
from .environment import Environment, global_env
from .base import Statement

from .callables import PoxFunction
from .expression import Expr
from .statement import Stmt
from .base import (
    Visitor,
    Expression,
    LiteralTypes,
    ParseError,
    literal2str,
    is_true,
    RunError,
)


class AstPrinter(Visitor):
    @singledispatchmethod
    def visit(self, expr: Expression | Statement) -> str:
        raise NotImplementedError(type(expr))

    @visit.register
    def _(self, expr: Expr.Binary) -> str:
        return (
            f"({self.visit(expr.left)}{expr.operator.lexeme}{self.visit(expr.right)})"
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


class Interpreter(Visitor):
    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    @singledispatchmethod
    def visit(self, expr: Expression, env: Environment = global_env) -> LiteralTypes:
        raise NotImplementedError(type(expr))

    @visit.register
    def _(self, expr: Expr.Binary, env: Environment = global_env) -> LiteralTypes:
        left = self.visit(expr.left, env)
        right = self.visit(expr.right, env)
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
        right = self.visit(expr.right, env)
        if expr.operator.token_type == TokenType.MINUS:
            if not isinstance(right, (float, int)):
                raise ParseError()
            return -1 * right
        elif expr.operator.token_type == TokenType.BANG:
            return bool(right)
        raise ParseError()

    @visit.register
    def _(self, expr: Expr.Grouping, env: Environment = global_env) -> LiteralTypes:
        return self.visit(expr.expr, env)

    @visit.register
    def _(self, expr: Expr.Variable, env: Environment = global_env) -> LiteralTypes:
        return env.get(expr.identify.lexeme)

    @visit.register
    def _(self, expr: Expr.Assign, env: Environment = global_env) -> LiteralTypes:
        env.assign(expr.identify.lexeme, self.visit(expr.value, env))

    @visit.register
    def _(self, stmt: Stmt.PrintStmt, env: Environment = global_env):
        string = literal2str(self.visit(stmt.expr, env))
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
    def _(self, stmt: Stmt.IF, env: Environment = global_env):
        if is_true(self.visit(stmt.condition, env)):
            self.visit(stmt.consequent, env)
        elif stmt.alternative:
            self.visit(stmt.alternative, env)

    @visit.register
    def _(self, expr: Expr.Logical, env: Environment = global_env):
        if expr.operator.token_type == TokenType.OR:
            if is_true(self.visit(expr.left, env)):
                return self.visit(expr.left, env)
            return self.visit(expr.right, env)
        elif expr.operator.token_type == TokenType.AND:
            if is_true(self.visit(expr.left, env)):
                return self.visit(expr.right, env)
            return self.visit(expr.left, env)
        else:
            raise RunError(f"Invalid Operator: {expr.operator.lexeme}")

    @visit.register
    def _(self, stmt: Stmt.While, env: Environment = global_env):
        while is_true(self.visit(stmt.condition, env)):
            self.visit(stmt.statement, env)

    @visit.register
    def _(self, expr: Expr.Call, env: Environment = global_env):
        callee = cast(PoxFunction, self.visit(expr.expr, env))
        arguments = [self.visit(arg) for arg in expr.arguments]
        if len(arguments) != callee.arity:
            raise RunError(f"实参数目:{len(arguments)} != 形参数目:{callee.arity}")
        env = Environment(env)
        for name, value in zip(callee.parameters, arguments):
            env.define(name , value)
        self.visit(callee.block, env)


    @visit.register
    def _(self, stmt: Stmt.Function, env: Environment = global_env):
        func = PoxFunction(stmt)
        env.define(stmt.name, func)
