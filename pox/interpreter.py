import sys
import logging
import time
from typing import cast, Optional, Any

from functools import singledispatchmethod
from .token import TokenType, Token
from .environment import Environment, global_env
from .base import Statement, ReturnException

from .callables import PoxFunction, PoxClass
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


logger = logging.getLogger(__name__)


class TimingFunction(PoxFunction):
    def __init__(self):
        pass

    def arity(self):
        return 0

    def to_str(self) -> str:
        return "<fun time>"

    def call(
        self,
        interpreter: Visitor,
        arguments: Optional[list[LiteralTypes]] = None,
    ):
        return time.time()


class Interpreter(Visitor):
    def __init__(self):
        global_env.define("time", TimingFunction())
        self.locals: dict[Expression, int] = dict()

    def resolve(self, locals: dict[Expression, int]):
        self.locals = {**locals}

    def lookup_variable(self, name: Token, expr: Expression, env: Environment) -> Any:
        distance = self.locals.get(expr)
        if distance is None:
            if name.lexeme not in global_env.vars:
                raise RunError(f"Cant find {name.lexeme} at line: {name.line}")
            return global_env.vars[name.lexeme]
        return env.get_at(name, distance)

    @singledispatchmethod
    def visit(
        self, expr: Expression | Statement, env: Environment = global_env
    ) -> LiteralTypes:
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
        return env.get(expr.identify)

    @visit.register
    def _(self, expr: Expr.Assign, env: Environment = global_env) -> LiteralTypes:
        env.assign(expr.identify, self.visit(expr.value, env))

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
    def _(self, expr: Expr.Call, env: Environment = global_env) -> LiteralTypes:
        callee = cast(PoxFunction, self.visit(expr.expr, env))
        arguments = [self.visit(arg, env) for arg in expr.arguments]
        return callee.call(self, arguments)

    @visit.register
    def _(self, stmt: Stmt.Function, env: Environment = global_env):
        func = PoxFunction(stmt, env)
        env.define(stmt.name, func)
        logger.info(f"@Funtion")

    @visit.register
    def _(self, stmt: Stmt.Return, env: Environment = global_env):
        raise ReturnException(self.visit(stmt.value, env))

    @visit.register
    def _(self, stmt: Stmt.Class, env: Environment = global_env):
        env.define(stmt.name, None)
        methods = [PoxFunction(m, env) for m in stmt.methods]
        cls = PoxClass(stmt.name, methods)
        env.assign(stmt.name, cls)
