from .token import Token, TokenType
from functools import singledispatchmethod
from .base import Visitor, ParseError, LiteralTypes, Expression, Statement
from .expression import Expr
from .statement import Stmt


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
        raise ParseError(err)

    def statement(self) -> Statement:
        if self.match_any(TokenType.PRINT):
            return self.print_stmt()
        return self.expr_stmt()

    def expr_stmt(self) -> Stmt.ExprStmt:
        return Stmt.ExprStmt()

    def print_stmt(self) -> Stmt.PrintStmt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        return Stmt.PrintStmt(expr)

    def parse(self) -> list[Statement]:
        statements: list[Statement] = list()
        while not self.is_end():
            stmt = self.statement()
            statements.append(stmt)
        return statements

    def expression(self) -> Expression:
        return self.equality()

    def comparision(self) -> Expression:
        expr = self.term()
        while self.match_any(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator = self.previous()
            right = self.term()
            expr = Expr.Binary(expr, operator, right)
        return expr

    def term(self) -> Expression:
        expr = self.factor()
        while self.match_any(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.factor()
            expr = Expr.Binary(expr, operator, right)
        return expr

    def factor(self) -> Expression:
        expr = self.unary()
        while self.match_any(TokenType.STAR, TokenType.SLASH):
            operator = self.previous()
            right = self.unary()
            expr = Expr.Binary(expr, operator, right)
        return expr

    def unary(self) -> Expression:
        if self.match_any(TokenType.MINUS, TokenType.BANG):
            return Expr.Unary(self.previous(), self.primary())
        return self.primary()

    def primary(self) -> Expression:
        if self.match_any(TokenType.TRUE):
            return Expr.Literal(True)
        if self.match_any(TokenType.FALSE):
            return Expr.Literal(False)
        if self.match_any(TokenType.NIL):
            return Expr.Literal(None)
        if self.match_any(TokenType.NUMBER, TokenType.STRING):
            return Expr.Literal(self.previous().literal)

        if self.match_any(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expressoin")
            return Expr.Grouping(expr)

        raise ParseError()

    def equality(self) -> Expression:
        expr = self.comparision()
        while self.match_any(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            right = self.comparision()
            expr = Expr.Binary(expr, self.previous(), right)
        return expr

    def number(self):
        return self.peek()
