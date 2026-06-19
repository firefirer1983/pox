from typing import Any
from enum import StrEnum


class TokenType(StrEnum):
    # 一个字符串的 TOKEN
    LEFT_PAREN = "LEFT_PAREN"  # "
    RIGHT_PAREN = "RIGHT_PAREN"  # "
    LEFT_BRACE = "LEFT_BRACE"  # (
    RIGHT_BRACE = "RIGHT_BRACE"  # )
    COMMA = "COMMA"  # ,
    DOT = "DOT"  # .
    MINUS = "MINUS"  # -
    PLUS = "PLUS"  # +
    SEMICOLON = "SEMICOLON"  # ;
    SLASH = "SLASH"  # /
    STAR = "STAR"  # *

    # 1个或者2个字符串的 TOKEN
    BANG = "BANG"  # !
    BANG_EQUAL = "BANG_EQUAL"  # !=
    EQUAL = "EQUAL"  # =
    EQUAL_EQUAL = "EQUAL_EQUAL"  # ==
    GREATER = "GREATER"  # >
    GREATER_EQUAL = "GREATER_EQUAL"  # >=
    LESS = "LESS"  # <
    LESS_EQUAL = "LESS_EQUAL"  # <=

    # 常量 Literals
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"

    # 关键字
    AND = "AND"
    CLASS = "CLASS"
    ELSE = "ELSE"
    FALSE = "FALSE"
    FUN = "FUN"
    FOR = "FOR"
    IF = "IF"
    NIL = "NIL"
    OR = "OR"
    PRINT = "PRINT"
    RETURN = "RETURN"
    SUPER = "SUPER"
    THIS = "THIS"
    TRUE = "TRUE"
    VAR = "VAR"
    WHILE = "WHILE"

    EOF = "EOF"


class Token:
    def __init__(self, lexeme: str, token_type: TokenType, literal: Any, line: int):
        self.lexeme = lexeme
        self.token_type = token_type
        self.literal = literal
        self.line = line

    def __repr__(self) -> str:
        return f"{self.token_type}('{self.lexeme}') @ {self.line}"

    def __str__(self) -> str:
        return repr(self)
