import logging

from .token import Token, TokenType
from .err import pox_error


logger = logging.getLogger(__name__)


class Parser:
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

    def add_string_literal(self) -> Token:
        string = ""
        while True:
            if self.peek() == '"':
                self.advance()
                break

            if self.is_end():
                pox_error(self.line, f'line: {self.line} 缺少"')
                return

            char = self.advance()
            if char == "\n":
                self.line += 1
            string += char

        token = Token(
            self.source[self.start + 1 : self.current - 1],
            TokenType.STRING,
            None,
            self.line,
        )
        self.tokens.append(token)
        return token

    def add_digit_literal(self) -> Token:
        while not self.is_end():
            if not (self.is_digit(self.peek()) or self.peek() == "."):
                break
            self.advance()
            continue
        token = Token(self.source[self.start: self.current], TokenType.NUMBER, None, self.line)
        self.tokens.append(token)



    def scan_tokens(self) -> list[Token]:
        while not self.is_end():
            char = self.advance()
            if char == "(":
                self.add_token(TokenType.LEFT_PAREN)
            elif char == ")":
                self.add_token(TokenType.RIGHT_PAREN)
            elif char == "{":
                self.add_token(TokenType.LEFT_BRACE)
            elif char == "}":
                self.add_token(TokenType.RIGHT_BRACE)
            elif char == ",":
                self.add_token(TokenType.COMMA)
            elif char == ".":
                self.add_token(TokenType.DOT)
            elif char == "-":
                self.add_token(TokenType.MINUS)
            elif char == "+":
                self.add_token(TokenType.PLUS)
            elif char == ";":
                self.add_token(TokenType.SEMICOLON)
            elif char == "/" and self.match("/"):
                comment = ""
                while not self.is_end() and self.peek() != "\n":
                    comment += self.advance()
                logger.info(f"COMMENT: {comment}")
                self.line += 1
            elif char == "/":
                self.add_token(TokenType.SLASH)
            elif char == "*":
                self.add_token(TokenType.STAR)
            elif char == "!":
                if self.match("="):
                    self.add_token(TokenType.BANG_EQUAL)
                else:
                    self.add_token(TokenType.BANG)
            elif char == "=":
                if self.match("="):
                    self.add_token(TokenType.EQUAL_EQUAL)
                else:
                    self.add_token(TokenType.EQUAL)
            elif char == ">":
                if self.match("="):
                    self.add_token(TokenType.GREATER_EQUAL)
                else:
                    self.add_token(TokenType.GREATER)
            elif char == "<":
                if self.match("="):
                    self.add_token(TokenType.LESS_EQUAL)
                else:
                    self.add_token(TokenType.LESS)
            elif char in (" ", "\t", "\r"):
                self.start = self.current
            elif char == "\n":
                self.line += 1
            elif char == '"':
                self.add_string_literal()
            elif self.is_digit(char):
                self.add_digit_literal()
            else:
                pox_error(
                    self.line,
                    f"错误的字符: {char} at line:{self.line}, column: {self.current}",
                )
                break
            self.start = self.current

        return self.tokens

    def is_digit(self) -> bool:
        return "0" <= self.source[self.current] <= "9"

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
