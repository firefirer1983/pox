from .token import Token, TokenType
from functools import singledispatchmethod
from .base import Visitor, ParseError, LiteralTypes, Expression, Statement
from .expression import Expr
from .statement import Stmt




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

    def equality(self) -> Expression:
        expr = self.comparision()
        while self.match_any(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            right = self.comparision()
            expr = Expr.Binary(expr, self.previous(), right)
        return expr

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

        if self.match_any(TokenType.IDENTIFIER):
            return Expr.Variable(self.previous())

        raise ParseError()

    def number(self):
        return self.peek()
