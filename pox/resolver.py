import logging
from typing import cast
from collections import deque
from functools import singledispatchmethod

from contextlib import contextmanager

from .base import Statement, ReturnException, ResolveError
from .expression import Expr
from .token import Token
from .statement import Stmt
from .callables import FunctionType, ClassType
from .base import (
    Visitor,
    Expression,
    LiteralTypes,
)


logger = logging.getLogger(__name__)


class Resolver(Visitor):
    def __init__(self):
        self.scopes: list[dict[str, bool]] = list()
        self.locals: dict[Expression, int] = dict()
        self.current_func_type = FunctionType.NONE
        self.current_class_type = ClassType.NONE

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

    def declare(self, name: Token):
        if self.is_empty:
            return
        scope = self.peek()
        if name.lexeme in scope:
            raise ResolveError(f"{name.lexeme} line: {name.line} is already exists")
        scope[name.lexeme] = False

    def define(self, name: Token):
        if self.is_empty:
            return
        scope = self.peek()
        scope[name.lexeme] = True

    def visit_many(self, stmts: list[Statement])-> dict[Expression, int]:
        for stmt in stmts:
            self.visit(stmt)
        return self.locals

    @singledispatchmethod
    def visit(self, expr: Expression | Statement) -> LiteralTypes:
        raise NotImplementedError(type(expr))

    def local_resolve(self, expr: Expression, name: str):
        for i, scope in enumerate(reversed(self.scopes)):
            if name not in scope:
                continue
            self.locals[expr] = i
            return

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
        if not self.is_empty:
            scope = self.peek()
            if expr.identify.lexeme in scope and not scope[expr.identify.lexeme]:
                raise ResolveError(
                    f"Can't read local variable {expr.identify.lexeme} before initialization."
                )
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
        self.declare(stmt.name)
        if stmt.initializer:
            self.visit(stmt.initializer)
        self.define(stmt.name)

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
        for arg in expr.arguments:
            self.visit(arg)
        self.visit(expr.expr)

    @visit.register
    def _(self, stmt: Stmt.Function):
        self.declare(stmt.name)
        self.define(stmt.name)
        self.function_resolve(stmt, FunctionType.FUNCTION)

    @visit.register
    def _(self, stmt: Stmt.Return):
        if self.current_func_type == FunctionType.NONE:
            raise ResolveError("Can't return from top level code.")
        value = cast(Expr.Literal, stmt.value)
        if self.current_func_type == FunctionType.INITIALIZER and value != None:
            raise ResolveError("Can't return a value from initializer.")
        if stmt.value:
            self.visit(stmt.value)

    @visit.register
    def _(self, stmt: Stmt.Class):
        enclosingClass = self.current_class_type
        self.current_class_type = ClassType.CLASS

        self.declare(stmt.name)
        self.define(stmt.name)
        with self.scoping():
            scope = self.peek()
            scope["this"] = True
            for method in stmt.methods:
                func_type = FunctionType.METHOD
                if method.name.lexeme == "init":
                    func_type = FunctionType.INITIALIZER
                self.function_resolve(method, func_type)
        self.current_class_type = enclosingClass

    @visit.register
    def _(self, expr: Expr.Get):
        self.visit(expr.obj)

    @visit.register
    def _(self, expr: Expr.Set):
        # 由于属性名称动态添加，因此无法在resolver做resolve
        self.visit(expr.obj)
        self.visit(expr.value)

    @visit.register
    def _(self, expr: Expr.This):
        if self.current_class_type == ClassType.NONE:
            raise ResolveError(f"use this outside of a class")
        self.local_resolve(expr, "this")

    def resolve(self, expr: Expression | Statement) -> int:
        match type(expr):
            case Stmt.ExprStmt:
                v = cast(Stmt.ExprStmt, expr)
                return self.locals[v.expr]
            case Expr.Assign | Expr.Variable:
                v = cast(Expression, expr)
                try:
                    return self.locals[v]
                except KeyError:
                    raise ResolveError(f"{expr}: {type(expr)} resolve failed!")
            case _:
                raise ResolveError(f"{expr}: {type(expr)}is not resolvable")
