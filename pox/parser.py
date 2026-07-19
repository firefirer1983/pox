from pox.statement import Function
import logging
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
logger.setLevel(logging.ERROR)


def yild_stmt(gen: Generator[Statement, None, None]) -> Statement:
    return next(iter(gen))


P = ParamSpec("P")
R = TypeVar("R")

BYPASS_LOG = True


def log_trace(f: Callable[P, R]) -> Callable[P, R]:
    if BYPASS_LOG:
        return f

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
    def cur(self) -> str:
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
                logger.error(f"ParseError: {exc}", exc_info=True)
                raise
                self.synchronize()
            else:
                statements.append(stmt)
        return statements

    @log_trace
    def declaration(self) -> Statement:
        if self.match(TokenType.CLASS):
            return self.class_declaration()

        if self.match(TokenType.FUN):
            return self.func_declaration()

        if self.match(TokenType.VAR):
            return self.var_declaration()

        return self.statement()

    @log_trace
    def class_declaration(self) -> Statement:
        name = self.consume(TokenType.IDENTIFIER, "Expect symbol for class name")
        methods: list[Stmt.Function] = []
        self.consume(TokenType.LEFT_BRACE, "Expect '{' after class name")
        while True:
            if self.match(TokenType.RIGHT_BRACE):
                break
            if self.is_end():
                raise ParseError("Expect '}' after '{'")
            func = self.func_declaration()
            methods.append(func)
        return Stmt.Class(name.lexeme, methods=methods)

    @log_trace
    def var_declaration(self) -> Statement:
        name = self.consume(TokenType.IDENTIFIER, "Expect Variable Name")
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration")
        logger.info(f"@Stmt.Var")
        return Stmt.Var(name, initializer)

    @log_trace
    def func_declaration(self) -> Stmt.Function:
        name = self.consume(TokenType.IDENTIFIER, "Expect function name")
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after function name")
        arguments = list()
        while not self.match(TokenType.RIGHT_PAREN):
            if self.match(TokenType.IDENTIFIER):
                arg = self.previous()
                arguments.append(arg)

            if self.match(TokenType.COMMA):
                continue

            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after (")
            break
        self.consume(TokenType.LEFT_BRACE, "Expect '{' after )")
        block = self.block()
        logger.info(f"@Stmt.Function")
        return Stmt.Function(name.lexeme, [arg.lexeme for arg in arguments], block)

    @log_trace
    def block(self) -> Stmt.Block:
        statements = list()
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_end():
            stmt = self.declaration()
            statements.append(stmt)
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block")
        logger.info(f"@Stmt.Block")
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
        logger.info(f"@Stmt.IF")
        return Stmt.IF(condition, consequent, alternative)

    @log_trace
    def while_stmt(self) -> Stmt.While:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after while")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if")
        body = self.statement()
        logger.info(f"@Stmt.While")
        return Stmt.While(condition, body)

    @log_trace
    def return_stmt(self) -> Stmt.Return:
        if self.match(TokenType.SEMICOLON):
            return Stmt.Return(Expr.Literal(None))

        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' end of return")
        return Stmt.Return(expr)

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
            logger.info(f"@Stmt.Block")
            return Stmt.Block([initializer, Stmt.While(cond, body)])
        logger.info(f"@Stmt.While")
        return Stmt.While(cond, body)

    @log_trace
    def statement(self) -> Statement:
        if self.match(TokenType.IF):
            return self.if_stmt()
        elif self.match(TokenType.PRINT):
            return self.print_stmt()
        elif self.match(TokenType.RETURN):
            return self.return_stmt()
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
        logger.info(f"@Stmt.ExprStmt")
        return Stmt.ExprStmt(expr)

    @log_trace
    def print_stmt(self) -> Stmt.PrintStmt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        logger.info(f"@Stmt.PrintStmt")
        return Stmt.PrintStmt(expr)

    @log_trace
    def expression(self) -> Expression:
        return self.assignment()

    @log_trace
    def assignment(self) -> Expression:
        expr = self.or_expr()
        if self.match(TokenType.EQUAL):
            # eq = self.previous()
            value = self.or_expr()
            if isinstance(expr, Expr.Variable):
                logger.info(f"@Expr.Assign")
                return Expr.Assign(expr.identify, value)
        return expr

    @log_trace
    def or_expr(self) -> Expression:
        left = self.and_expr()
        if self.match(TokenType.OR):
            token = self.previous()
            right = self.and_expr()
            logger.info(f"@Expr.Logical")
            return Expr.Logical(left, token, right)
        return left

    @log_trace
    def and_expr(self) -> Expression:
        left = self.equality()
        if self.match(TokenType.AND, TokenType.OR):
            token = self.previous()
            right = self.or_expr()
            logger.info(f"@Expr.Logical")
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

    def _call(self, expr) -> Expr.Call:
        arguments = list()
        while not self.match(TokenType.RIGHT_PAREN):
            arg = self.expression()
            arguments.append(arg)
            if not self.match(TokenType.COMMA):
                self.consume(
                    TokenType.RIGHT_PAREN, "Expect ')' after function argment list"
                )
                break
            logger.info("@Expr.Call")
        return Expr.Call(expr, arguments)

    @log_trace
    def call(self) -> Expression:
        expr = self.primary()
        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self._call(expr)
                continue

            if self.match(TokenType.DOT):
                attr = self.consume(TokenType.IDENTIFIER, "Expect symbol after '.'")
                expr = Expr.GetAttr(expr, attr.lexeme)
                continue

            break

        return expr

    @log_trace
    def unary(self) -> Expression:
        if self.match(TokenType.MINUS, TokenType.BANG):
            logger.info("@Expr.Unary")
            return Expr.Unary(self.previous(), self.unary())
        return self.call()

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

        raise ParseError(f"Error Token: '{self.peek().lexeme}'")

    @log_trace
    def number(self):
        return self.peek()
