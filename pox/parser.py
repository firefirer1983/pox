from typing import Any
from .token import Token, TokenType
import abc
from abc import ABC, abstractmethod
from functools import singledispatchmethod

LiteralTypes = bool | str | int | float | None


class Visitor(abc.ABC):
    @singledispatchmethod
    @abstractmethod
    def visit(self, expr: "Expr") -> Any:
        raise NotImplementedError()


class Expr(ABC):
    def accept(self, visitor: Visitor):
        return visitor.visit(self)


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

    # def accept(self, visitor: Expr.Visitor):
    #     return visitor.visit(self)


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr):
        self.operator = operator
        self.right = right

    # def accept(self, visitor: Expr.Visitor):
    #     return visitor.visit(self)


class Literal(Expr):
    def __init__(self, value: LiteralTypes):
        self.value = value

    # def accept(self, visitor: Expr.Visitor):
    #     return visitor.visit(self)


class Grouping(Expr):
    def __init__(self, expr: Expr):
        self.expr = expr


class AstPrinter(Visitor):
    @singledispatchmethod
    def visit(self, expr: Expr) -> str:
        raise NotImplementedError(type(expr))

    @visit.register
    def _(self, expr: Binary) -> str:
        return (
            f"({expr.operator.lexeme} {self.visit(expr.left)} {self.visit(expr.right)})"
        )

    @visit.register
    def _(self, expr: Literal) -> str:
        return f"{expr.value}"

    @visit.register
    def _(self, expr: Unary) -> str:
        return f"{expr.operator.lexeme}{self.visit(expr.right)}"

    @visit.register
    def _(self, expr: Grouping) -> str:
        return f"({self.visit(expr.expr)})"


class Interpreter(Visitor):
    @singledispatchmethod
    def visit(self, expr: Expr) -> LiteralTypes:
        raise NotImplementedError(type(expr))

    @visit.register
    def _(self, expr: Binary) -> LiteralTypes:
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
                raise RuntimeError()

    @visit.register
    def _(self, expr: Literal) -> LiteralTypes:
        return expr.value

    @visit.register
    def _(self, expr: Unary) -> LiteralTypes:
        right = self.visit(expr.right)
        if expr.operator.token_type == TokenType.MINUS:
            if not isinstance(right, (float, int)):
                raise RuntimeError
            return -1 * right
        elif expr.operator.token_type == TokenType.BANG:
            return bool(right)
        raise RuntimeError

    @visit.register
    def _(self, expr: Grouping) -> LiteralTypes:
        return self.visit(expr.expr)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.start = self.current = 0

    def peek(self) -> Token:
        return self.tokens[self.current]

    def is_end(self) -> bool:
        return (
            len(self.tokens) == self.current or self.peek().token_type == TokenType.EOF
        )

    def is_begining(self):
        return self.current == 0

    def check(self, token_type: TokenType) -> bool:
        if self.is_end():
            return False
        return self.peek().token_type == token_type

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def advance(self) -> Token:
        if not self.is_end():
            self.current += 1
        return self.previous()

    def match_any(self, *expected_types: TokenType) -> bool:
        if self.is_end():
            return False

        for token_type in expected_types:
            if not self.check(token_type):
                continue
            self.advance()
            return True
        return False

    def consume(self, expect_type: TokenType, err: str):
        if self.check(expect_type):
            self.advance()
        raise RuntimeError(err)

    def expression(self) -> Expr:
        return self.equality()

    def comparision(self) -> Expr:
        expr = self.term()
        while self.match_any(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator = self.previous()
            right = self.term()
            expr = Binary(expr, operator, right)
        return expr

    def term(self) -> Expr:
        expr = self.factor()
        while self.match_any(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)
        return expr

    def factor(self) -> Expr:
        expr = self.unary()
        while self.match_any(TokenType.STAR, TokenType.SLASH):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)
        return expr

    def unary(self) -> Expr:
        if self.match_any(TokenType.MINUS, TokenType.BANG):
            return Unary(self.previous(), self.primary())
        return self.primary()

    def primary(self) -> Expr:
        if self.match_any(TokenType.TRUE):
            return Literal(True)
        if self.match_any(TokenType.FALSE):
            return Literal(False)
        if self.match_any(TokenType.NIL):
            return Literal(None)
        if self.match_any(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)

        if self.match_any(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expressoin")
            return Grouping(expr)
        raise RuntimeError

    def equality(self) -> Expr:
        expr = self.comparision()
        while self.match_any(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            right = self.comparision()
            expr = Binary(expr, self.previous(), right)
        return expr

    def number(self):
        return self.peek()
