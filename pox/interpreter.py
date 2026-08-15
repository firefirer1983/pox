from pox.resolver import Resolver
from pox.base import PoxCallable
from pox.callables import PoxInstance
import sys
import logging
import time
from typing import cast, Optional, Any

from functools import singledispatchmethod
from .token import TokenType, Token
from .environment import Environment
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

    def __repr__(self) -> str:
        return self.to_str()

    def __str__(self):
        return repr(self)


class Interpreter(Visitor):
    def __init__(self):
        self.global_env = Environment()
        self.env = self.global_env
        self.env.define("time", TimingFunction())
        self.locals: dict[Expression, int] = dict()
        self.resolver = Resolver()

    def lookup_variable(self, name: Token, expr: Expression, env: Environment) -> Any:
        distance = self.locals.get(expr)
        if distance is None:
            if name.lexeme not in self.global_env.vars:
                raise RunError(f"Cant find {name.lexeme} at line: {name.line}")
            return self.global_env.get(name)
        return env.get_at(name, distance)

    def visit_many(self, statements: list[Statement]):
        self.locals = {**self.resolver.visit_many(statements)}
        for stmt in statements:
            self.visit(stmt)

    @singledispatchmethod
    def visit(self, expr: Expression | Statement) -> Any:
        raise NotImplementedError(type(expr))

    @visit.register
    def _(self, expr: Expr.Binary) -> LiteralTypes:
        left = self.visit(expr.left)
        right = self.visit(expr.right)
        try:
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
        except (TypeError, ZeroDivisionError) as exc:
            logger.error("二进制运输错误", exc_info=True)
            raise RunError(f"{left} {expr.operator} {right} 二进制运输错误")

    @visit.register
    def _(self, expr: Expr.Literal) -> LiteralTypes:
        return expr.value

    @visit.register
    def _(self, expr: Expr.Unary) -> LiteralTypes:
        right = self.visit(expr.right)
        if expr.operator.token_type == TokenType.MINUS:
            if not isinstance(right, (float, int)):
                raise RunError(f"Syntax error, {right} is not number!")
            return -1 * right
        elif expr.operator.token_type == TokenType.BANG:
            return not is_true(right)
        raise ParseError()

    @visit.register
    def _(self, expr: Expr.Grouping) -> LiteralTypes:
        return self.visit(expr.expr)

    @visit.register
    def _(self, expr: Expr.Variable) -> LiteralTypes:
        return self.lookup_variable(expr.identify, expr, self.env)

    @visit.register
    def _(self, expr: Expr.Assign) -> LiteralTypes:
        value = self.visit(expr.value)
        if expr.value in self.locals:
            self.env.assign_at(expr.identify, value, self.locals[expr.value])
        else:
            self.global_env.assign(expr.identify, value)
        return value

    @visit.register
    def _(self, stmt: Stmt.PrintStmt):
        string = literal2str(self.visit(stmt.expr))
        sys.stdout.write(string + "\n")
        sys.stdout.flush()

    @visit.register
    def _(self, stmt: Stmt.ExprStmt):
        return self.visit(stmt.expr)

    @visit.register
    def _(self, stmt: Stmt.Var):
        value = None
        if stmt.initializer:
            value = self.visit(stmt.initializer, self.env)
        self.env.define(stmt.name.lexeme, value)

    @visit.register
    def _(self, stmt: Stmt.Block):
        enclosing = self.env
        try:
            self.env = Environment(self.env)
            for statement in stmt.statements:
                self.visit(statement)
        finally:
            self.env = enclosing

    @visit.register
    def _(self, stmt: Stmt.IF):
        if is_true(self.visit(stmt.condition)):
            self.visit(stmt.consequent)
        elif stmt.alternative:
            self.visit(stmt.alternative)

    @visit.register
    def _(self, expr: Expr.Logical):
        left = self.visit(expr.left)
        if expr.operator.token_type == TokenType.OR:
            return left if is_true(left) else self.visit(expr.right)
        elif expr.operator.token_type == TokenType.AND:
            if not is_true(left):
                return left
            return self.visit(expr.right)
        else:
            raise RunError(f"Invalid Operator: {expr.operator.lexeme}")

    @visit.register
    def _(self, stmt: Stmt.While):
        while is_true(self.visit(stmt.condition)):
            self.visit(stmt.statement)

    @visit.register
    def _(self, expr: Expr.Call) -> LiteralTypes:
        callee = self.visit(expr.expr)
        if isinstance(callee, PoxCallable):
            arguments = [self.visit(arg) for arg in expr.arguments]
            return callee.call(self, arguments)
        raise RunError(f"{callee} is not PoxFunction")

    @visit.register
    def _(self, stmt: Stmt.Function):
        func = PoxFunction(stmt, self.env)
        self.env.define(stmt.name.lexeme, func)
        logger.info(f"@Funtion")

    @visit.register
    def _(self, stmt: Stmt.Return):
        raise ReturnException(self.visit(stmt.value))

    @visit.register
    def _(self, stmt: Stmt.Class):
        self.env.define(stmt.name.lexeme, None)
        methods: list[PoxFunction] = list()
        for m in stmt.methods:
            initializer = False
            if m.name.lexeme == "init":
                initializer = True
            methods.append(PoxFunction(m, self.env, initializer))
        cls = PoxClass(stmt.name, methods)
        self.env.assign(stmt.name, cls)

    @visit.register
    def _(self, expr: Expr.Get):
        instance = self.visit(expr.obj)
        if not isinstance(instance, PoxInstance):
            raise RunError(f"{type(instance)} is not instance")
        return instance.get(expr.name)

    @visit.register
    def _(self, expr: Expr.Set):
        instance = self.visit(expr.obj)
        if not isinstance(instance, PoxInstance):
            raise RunError(f"{type(instance)} is not instance")
        value = self.visit(expr.value)
        instance.set(expr.name, value)
        return value

    @visit.register
    def _(self, expr: Expr.This):
        return self.lookup_variable(expr.keyword, expr, self.env)
