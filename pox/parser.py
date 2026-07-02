from typing import Generator
import logging

from .token import Token, TokenType
from .base import ParseError, Expression, Statement
from .expression import Expr
from .statement import Stmt


logger = logging.getLogger(__name__)


def yild_stmt(gen: Generator[Statement, None, None]) -> Statement:
    return next(iter(gen))


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

    def consume(self, expect_type: TokenType, err: str) -> Token:
        if self.check(expect_type):
            return self.advance()
        raise ParseError(err)

    def synchronize(self):
        pass

    def match(self, *expected_types: TokenType) -> bool:
        if self.is_end():
            return False

        for token_type in expected_types:
            if not self.check(token_type):
                continue
            self.advance()
            return True
        return False

    def parse(self) -> list[Statement]:
        statements = list()
        while not self.is_end():
            try:
                stmt = self.declaration()
            except ParseError as exc:
                logger.info(f"ParseError: {exc}", exc_info=True)
                self.synchronize()
            else:
                statements.append(stmt)
        return statements

    def declaration(self) -> Statement:
        if self.match(TokenType.VAR):
            return self.var_declaration()
        return self.statement()

    def var_declaration(self) -> Statement:
        name = self.consume(TokenType.IDENTIFIER, "Expect Variable Name")
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration")
        return Stmt.Var(name, initializer)

    def block(self) -> Statement:
        statements = list()
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_end():
            stmt = self.declaration()
            statements.append(stmt)
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block")
        return Stmt.Block(statements)

    def if_stmt(self) -> Stmt.IF:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after if")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if")
        consequent = self.statement()
        alternative = None
        if self.match(TokenType.ELSE):
            alternative = self.statement()
        return Stmt.IF(condition, consequent, alternative)

    def statement(self) -> Statement:
        if self.match(TokenType.IF):
            return self.if_stmt()
        elif self.match(TokenType.PRINT):
            return self.print_stmt()
        elif self.match(TokenType.LEFT_BRACE):
            return self.block()
        else:
            return self.expr_stmt()

    def expr_stmt(self) -> Stmt.ExprStmt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        return Stmt.ExprStmt(expr)

    def print_stmt(self) -> Stmt.PrintStmt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        return Stmt.PrintStmt(expr)


    def expression(self) -> Expression:
        return self.assignment()

    def assignment(self) -> Expression:
        expr = self.or_expr()
        if self.match(TokenType.EQUAL):
            eq = self.previous()
            value = self.or_expr()
            if isinstance(expr, Expr.Variable):
                return Expr.Assign(expr.identify, value)
            raise ParseError("Invalid assignment target")
        return expr

    def or_expr(self)-> Expression:
        left = self.and_expr()
        if self.match(TokenType.OR):
            token = self.previous()
            right = self.and_expr()
            return Expr.Logical(left, token, right)
        return left

    def and_expr(self) -> Expression:
        left = self.equality()
        if self.match(TokenType.AND):
            token = self.previous()
            right = self.equality()
            return Expr.Logical(left, token, right)
        return left

    def equality(self) -> Expression:
        expr = self.comparision()
        while self.match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            right = self.comparision()
            expr = Expr.Binary(expr, self.previous(), right)
        return expr

    def comparision(self) -> Expression:
        expr = self.term()
        while self.match(
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
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.factor()
            expr = Expr.Binary(expr, operator, right)
        return expr

    def factor(self) -> Expression:
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH):
            operator = self.previous()
            right = self.unary()
            expr = Expr.Binary(expr, operator, right)
        return expr

    def unary(self) -> Expression:
        if self.match(TokenType.MINUS, TokenType.BANG):
            return Expr.Unary(self.previous(), self.primary())
        return self.primary()

    def primary(self) -> Expression:
        if self.match(TokenType.TRUE):
            return Expr.Literal(True)

        if self.match(TokenType.FALSE):
            return Expr.Literal(False)

        if self.match(TokenType.NIL):
            return Expr.Literal(None)

        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Expr.Literal(self.previous().literal)

        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expressoin")
            return Expr.Grouping(expr)

        if self.match(TokenType.IDENTIFIER):
            return Expr.Variable(self.previous())

        raise ParseError()

    def number(self):
        return self.peek()
