from typing import Optional
from pox.token import key_words
import logging

from .token import Token, TokenType
from .err import pox_error


logger = logging.getLogger(__name__)


def is_digit(c: str) -> bool:
    return "0" <= c <= "9"


def is_alpha(c: str) -> bool:
    return "A" <= c <= "Z" or "a" <= c <= "z" or c == "_"


def is_alpha_or_number(c: str) -> bool:
    return is_digit(c) or is_alpha(c)


class Scanner:
    def __init__(self, source: str):
        self.source = source
        self.current = 0
        self.start = 0
        self.line = 1
        self.tokens: list[Token] = list()

    def add_token(self, token_type: TokenType) -> Token:
        token = Token(
            self.source[self.start : self.current], token_type, None, self.line
        )
        self.tokens.append(token)
        return token

    def add_string_literal(self) -> Optional[Token]:
        while True:
            if self.peek() in ('"', "'"):
                self.advance()
                break

            if self.is_end():
                pox_error(self.line, f'line: {self.line} 缺少"')
                return

            if self.advance() == "\n":
                self.line += 1

        token = Token(
            self.source[self.start + 1 : self.current - 1],
            TokenType.STRING,
            self.source[self.start + 1 : self.current - 1],
            self.line,
        )
        self.tokens.append(token)
        return token

    def add_digit_literal(self) -> Optional[Token]:
        while not self.is_end():
            if not (is_digit(self.peek()) or self.peek() == "."):
                break
            self.advance()
            continue
        lexeme = self.source[self.start : self.current]
        if "." in lexeme:
            literal = float(lexeme)
        else:
            literal = int(lexeme)
        token = Token(lexeme, TokenType.NUMBER, literal, self.line)
        self.tokens.append(token)

    def add_identifier(self) -> Optional[Token]:
        while not self.is_end():
            if not is_alpha_or_number(self.peek()):
                break
            self.advance()

        token_type = (
            key_words.get(self.source[self.start : self.current])
            or TokenType.IDENTIFIER
        )
        self.add_token(token_type)

    def scan_tokens(self) -> list[Token]:
        while not self.is_end():
            c = self.advance()
            if c == "(":
                self.add_token(TokenType.LEFT_PAREN)
            elif c == ")":
                self.add_token(TokenType.RIGHT_PAREN)
            elif c == "{":
                self.add_token(TokenType.LEFT_BRACE)
            elif c == "}":
                self.add_token(TokenType.RIGHT_BRACE)
            elif c == ",":
                self.add_token(TokenType.COMMA)
            elif c == ".":
                self.add_token(TokenType.DOT)
            elif c == "-":
                self.add_token(TokenType.MINUS)
            elif c == "+":
                self.add_token(TokenType.PLUS)
            elif c == ";":
                self.add_token(TokenType.SEMICOLON)
            elif c == "/" and self.match("/"):
                comment = ""
                while not self.is_end() and self.peek() != "\n":
                    comment += self.advance()
                logger.info(f"COMMENT: {comment}")
                self.line += 1
            elif c == "/":
                self.add_token(TokenType.SLASH)
            elif c == "*":
                self.add_token(TokenType.STAR)
            elif c == "!":
                if self.match("="):
                    self.add_token(TokenType.BANG_EQUAL)
                else:
                    self.add_token(TokenType.BANG)
            elif c == "=":
                if self.match("="):
                    self.add_token(TokenType.EQUAL_EQUAL)
                else:
                    self.add_token(TokenType.EQUAL)
            elif c == ">":
                if self.match("="):
                    self.add_token(TokenType.GREATER_EQUAL)
                else:
                    self.add_token(TokenType.GREATER)
            elif c == "<":
                if self.match("="):
                    self.add_token(TokenType.LESS_EQUAL)
                else:
                    self.add_token(TokenType.LESS)
            elif c in (" ", "\t", "\r"):
                pass
            elif c == "\n":
                self.line += 1
            elif c in ("'", '"'):
                self.add_string_literal()
            elif is_digit(c):
                self.add_digit_literal()
            elif is_alpha(c):
                self.add_identifier()
            else:
                pox_error(
                    self.line,
                    f"错误的字符: {c} at line:{self.line}, column: {self.current}",
                )
                break
            self.start = self.current

        return self.tokens

    def is_end(self) -> bool:
        return self.current >= len(self.source)

    def peek(self) -> str:
        return self.source[self.current]

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        return char

    def match(self, expected: str) -> bool:
        if self.is_end() or self.source[self.current] != expected:
            return False

        self.current += 1
        return True
