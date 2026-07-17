import logging
from typing import cast
from collections import deque
from functools import singledispatchmethod

from contextlib import contextmanager

from .base import Statement, ReturnException, ResolveError

from .expression import Expr
from .statement import Stmt
from .callables import FunctionType
from .base import (
    Visitor,
    Expression,
    LiteralTypes,
)

logger = logging.getLogger(__name__)


class Resolver(Visitor):
    def __init__(self):
        self.scopes: deque[dict[str, bool]] = deque()
        self.scopes.append(dict())
        self.locals: dict[Expression, int] = dict()
        self.current_func_type = FunctionType.NONE

    @contextmanager
    def scoping(self):
        var_map: dict[str, bool] = dict()
        self.scopes.append(var_map)
        yield
        self.scopes.pop()

    @property
    def is_empty(self) -> bool:
        return not bool(self.scopes)

    def peek(self) -> dict[str, bool]:
        return self.scopes[-1]

    def declare(self, name: str):
        if self.is_empty:
            raise ResolveError(f"Scope Empty!")

        scope = self.peek()
        if name in scope:
            raise ResolveError(f"{name} is already exists")
        scope[name] = False

    def define(self, name: str):
        if self.is_empty:
            raise ResolveError(f"Scope Empty!")
        scope = self.peek()
        scope[name] = True

    def visit_many(self, stmts: list[Statement]):
        for stmt in stmts:
            self.visit(stmt)

    @singledispatchmethod
    def visit(self, expr: Expression | Statement) -> LiteralTypes:
        raise NotImplementedError(type(expr))

    def local_resolve(self, expr: Expression, name: str):
        for i, scope in enumerate(reversed(self.scopes)):
            if name in scope:
                self.locals[expr] = i
                return
        raise ResolveError(f"Resolve {name} failed!")

    def function_resolve(self, stmt: Stmt.Function, func_type: FunctionType):
        encolsing_func_type = self.current_func_type
        self.current_func_type = func_type
        with self.scoping():
            for arg in stmt.parameters:
                self.declare(arg)
                self.define(arg)
            self.visit(stmt.block)
        self.current_func_type = encolsing_func_type

    @visit.register
    def _(self, expr: Expr.Binary):
        self.visit(expr.left)
        self.visit(expr.right)

    @visit.register
    def _(self, expr: Expr.Literal):
        return expr.value

    @visit.register
    def _(self, expr: Expr.Unary):
        self.visit(expr.right)

    @visit.register
    def _(self, expr: Expr.Grouping) -> LiteralTypes:
        return self.visit(expr.expr)

    @visit.register
    def _(self, expr: Expr.Variable) -> LiteralTypes:
        if not self.is_empty and not self.peek().get(expr.identify.lexeme):
            raise ResolveError(f"Can't read local variable {expr.identify.lexeme} in its own initializer.")
        self.local_resolve(expr, expr.identify.lexeme)

    @visit.register
    def _(self, expr: Expr.Assign) -> LiteralTypes:
        self.visit(expr.value)
        self.local_resolve(expr, expr.identify.lexeme)

    @visit.register
    def _(self, stmt: Stmt.PrintStmt):
        self.visit(stmt.expr)

    @visit.register
    def _(self, stmt: Stmt.ExprStmt):
        self.visit(stmt.expr)

    @visit.register
    def _(self, stmt: Stmt.Var):
        self.declare(stmt.name.lexeme)
        if stmt.initializer:
            self.visit(stmt.initializer)
        self.define(stmt.name.lexeme)

    @visit.register
    def _(self, stmt: Stmt.Block):
        with self.scoping():
            for statement in stmt.statements:
                self.visit(statement)

    @visit.register
    def _(self, stmt: Stmt.IF):
        self.visit(stmt.condition)
        self.visit(stmt.consequent)
        if not stmt.alternative:
            return
        self.visit(stmt.alternative)

    @visit.register
    def _(self, expr: Expr.Logical):
        self.visit(expr.left)
        self.visit(expr.right)

    @visit.register
    def _(self, stmt: Stmt.While):
        self.visit(stmt.condition)
        self.visit(stmt.statement)

    @visit.register
    def _(self, expr: Expr.Call) -> LiteralTypes:
        self.visit(expr.expr)
        for arg in expr.arguments:
            self.visit(arg)

    @visit.register
    def _(self, stmt: Stmt.Function):
        self.declare(stmt.name)
        self.define(stmt.name)
        self.function_resolve(stmt, FunctionType.FUNCTION)

    @visit.register
    def _(self, stmt: Stmt.Return):
        raise ReturnException(self.visit(stmt.value))

    def resolve(self, expr: Expression | Statement) -> int:
        match type(expr):
            case Stmt.ExprStmt:
                v = cast(Stmt.ExprStmt, expr)
                return self.locals[v.expr]
            case Expr.Assign | Expr.Binary | Expr.Call | Expr.Grouping | Expr.Logical | Expr.Unary | Expr.Variable:
                v = cast(Expression, expr)
                return self.locals[v]
            case _:
                raise ResolveError(f"{expr} is not resolvable")
