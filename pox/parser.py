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

    def scan_tokens(self) -> list[Token]:
        tokens: list[Token] = list()
        while not self.is_end():
            char = self.advance()
            if char == '(':
                tokens.append(Token(char, TokenType.LEFT_PAREN, None, self.line))
            elif char == ')':
                tokens.append(Token(char, TokenType.RIGHT_PAREN, None, self.line))
            elif char == "{":
                tokens.append(Token(char, TokenType.LEFT_BRACE, None, self.line))
            elif char == "}":
                tokens.append(Token(char, TokenType.RIGHT_BRACE, None, self.line))
            elif char == ",":
                tokens.append(Token(char, TokenType.COMMA, None, self.line))
            elif char == ".":
                tokens.append(Token(char, TokenType.DOT, None, self.line))
            elif char == "-":
                tokens.append(Token(char, TokenType.MINUS, None, self.line))
            elif char == "+":
                tokens.append(Token(char, TokenType.PLUS, None, self.line))
            elif char == ";":
                tokens.append(Token(char, TokenType.SEMICOLON, None, self.line))
            elif char == "/" and self.match("/"):
                comment = ""
                while not self.is_end() and self.peek() != "\n":
                    comment += self.advance()
                logger.info(f"COMMENT: {comment}")
            elif char == "/":
                tokens.append(Token(char, TokenType.SLASH, None, self.line))
            elif char == "*":
                tokens.append(Token(char, TokenType.STAR, None, self.line))
            elif char == "!":
                token_type = TokenType.BANG
                if self.match("="):
                    token_type = TokenType.BANG_EQUAL
                tokens.append(Token(char, token_type, None, self.line))
            elif char == "=":
                token_type = TokenType.EQUAL
                if self.match("="):
                    token_type = TokenType.EQUAL_EQUAL
                tokens.append(Token(char, token_type, None, self.line))
            elif char == ">":
                token_type = TokenType.GREATER
                if self.match("="):
                    token_type = TokenType.GREATER_EQUAL
                tokens.append(Token(char, token_type, None, self.line))
            elif char == "<":
                token_type = TokenType.LESS
                if self.match("="):
                    token_type = TokenType.LESS_EQUAL
                tokens.append(Token(char, token_type, None, self.line))
            elif char in (" ", "\t", "\r"):
                pass
            elif char == "\n":
                self.line = self.line + 1
            else:
                pox_error(
                    self.line,
                    f"错误的字符: {char} at line:{self.line}, column: {self.current}",
                )
                break

        return tokens

    def is_end(self) -> bool:
        return self.current >= len(self.source)

    def peek(self) -> str:
        return self.source[self.current + 1]

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        return char

    def match(self, expected: str) -> bool:
        if self.is_end() or self.source[self.current] != expected:
            return False

        self.current += 1
        return True
