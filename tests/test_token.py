import pytest
from pox.token import Token, TokenType


class TestTokenType:
    def test_token_type_has_correct_values(self):
        assert TokenType.LEFT_PAREN == "LEFT_PAREN"
        assert TokenType.RIGHT_PAREN == "RIGHT_PAREN"
        assert TokenType.PLUS == "PLUS"
        assert TokenType.MINUS == "MINUS"

    def test_token_type_is_str_enum(self):
        assert isinstance(TokenType.TRUE, str)


class TestToken:
    def test_token_creation(self):
        token = Token("foo", TokenType.IDENTIFIER, "bar", 1)
        assert token.lexeme == "foo"
        assert token.token_type == TokenType.IDENTIFIER
        assert token.literal == "bar"
        assert token.line == 1
