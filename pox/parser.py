from typing import Callable
from functools import wraps
from typing import Generator
import logging
from typing import Callable, TypeVar, ParamSpec

from .token import Token, TokenType
from .base import ParseError, Expression, Statement
from .expression import Expr
from .statement import Stmt


logger = logging.getLogger(__name__)


def yild_stmt(gen: Generator[Statement, None, None]) -> Statement:
    return next(iter(gen))

P = ParamSpec("P")
R = TypeVar("R")

def log_trace(f: Callable[P, R]) -> Callable[P, R]:
    @wraps(f)
    def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.info(f"% {f.__name__}")
        return f(*args, **kwargs)

    return _wrapper


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.start = self.current = 0

    @property
    def t(self)-> str:
        tkn = self.tokens[self.current]
        return f"<{tkn.token_type}({tkn.lexeme})>"

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

    @log_trace
    def declaration(self) -> Statement:
        if self.match(TokenType.VAR):
            return self.var_declaration()
        return self.statement()

    @log_trace
    def var_declaration(self) -> Statement:
        name = self.consume(TokenType.IDENTIFIER, "Expect Variable Name")
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration")
        return Stmt.Var(name, initializer)

    @log_trace
    def block(self) -> Stmt.Block:
        statements = list()
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_end():
            stmt = self.declaration()
            statements.append(stmt)
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block")
        return Stmt.Block(statements)

    @log_trace
    def if_stmt(self) -> Stmt.IF:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after if")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if")
        consequent = self.statement()
        alternative = None
        if self.match(TokenType.ELSE):
            alternative = self.statement()
        return Stmt.IF(condition, consequent, alternative)

    @log_trace
    def while_stmt(self)-> Stmt.While:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after while")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if")
        body = self.statement()
        return Stmt.While(condition, body)

    @log_trace
    def for_stmt(self) -> Stmt.While | Stmt.Block:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after for")
        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = Stmt.ExprStmt(self.expression())
            self.consume(TokenType.SEMICOLON, "Exprect ';' after initialier")

        cond = Expr.Literal(True)
        if not self.check(TokenType.SEMICOLON):
            cond = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after for")

        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for")
        self.consume(TokenType.LEFT_BRACE, "Expect '{' after for")
        body = self.block()
        if increment:
            body.statements = body.statements + [Stmt.ExprStmt(increment)]

        if initializer:
            return Stmt.Block([initializer, Stmt.While(cond, body)])
        return Stmt.While(cond, body)

    @log_trace
    def statement(self) -> Statement:
        if self.match(TokenType.IF):
            return self.if_stmt()
        elif self.match(TokenType.PRINT):
            return self.print_stmt()
        elif self.match(TokenType.FOR):
            return self.for_stmt()
        elif self.match(TokenType.WHILE):
            return self.while_stmt()
        elif self.match(TokenType.LEFT_BRACE):
            return self.block()
        else:
            return self.expr_stmt()

    @log_trace
    def expr_stmt(self) -> Stmt.ExprStmt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        return Stmt.ExprStmt(expr)

    @log_trace
    def print_stmt(self) -> Stmt.PrintStmt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        return Stmt.PrintStmt(expr)

    @log_trace
    def expression(self) -> Expression:
        return self.assignment()

    @log_trace
    def assignment(self) -> Expression:
        expr = self.or_expr()
        if self.match(TokenType.EQUAL):
            eq = self.previous()
            value = self.or_expr()
            if isinstance(expr, Expr.Variable):
                return Expr.Assign(expr.identify, value)
        return expr

    @log_trace
    def or_expr(self) -> Expression:
        left = self.and_expr()
        if self.match(TokenType.OR):
            token = self.previous()
            right = self.and_expr()
            return Expr.Logical(left, token, right)
        return left

    @log_trace
    def and_expr(self) -> Expression:
        left = self.equality()
        if self.match(TokenType.AND, TokenType.OR):
            token = self.previous()
            right = self.or_expr()
            return Expr.Logical(left, token, right)
        return left

    @log_trace
    def equality(self) -> Expression:
        expr = self.comparision()
        while self.match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            right = self.comparision()
            expr = Expr.Binary(expr, self.previous(), right)
        return expr

    @log_trace
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

    @log_trace
    def term(self) -> Expression:
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.factor()
            expr = Expr.Binary(expr, operator, right)
        return expr

    @log_trace
    def factor(self) -> Expression:
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH):
            operator = self.previous()
            right = self.unary()
            expr = Expr.Binary(expr, operator, right)
        return expr

    @log_trace
    def unary(self) -> Expression:
        if self.match(TokenType.MINUS, TokenType.BANG):
            return Expr.Unary(self.previous(), self.primary())
        return self.primary()

    @log_trace
    def primary(self) -> Expression:
        if self.match(TokenType.TRUE):
            logger.info("@Literal<true>")
            return Expr.Literal(True)

        if self.match(TokenType.FALSE):
            logger.info("@Literal<false>")
            return Expr.Literal(False)

        if self.match(TokenType.NIL):
            logger.info("@Literal<nil>")
            return Expr.Literal(None)

        if self.match(TokenType.NUMBER):
            logger.info("@Literal<number>")
            return Expr.Literal(self.previous().literal)

        if self.match(TokenType.STRING):
            logger.info("@Literal<string>")
            return Expr.Literal(self.previous().literal)

        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expressoin")
            logger.info("@Grouping")
            return Expr.Grouping(expr)

        if self.match(TokenType.IDENTIFIER):
            logger.info("@Var")
            return Expr.Variable(self.previous())

        raise ParseError(f"Error Token: {self.peek().lexeme}")

    @log_trace
    def number(self):
        return self.peek()
