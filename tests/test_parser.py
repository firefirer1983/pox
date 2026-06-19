import pytest
from pox.parser import Parser
from pox.token import TokenType


class TestParseSingleToken:
    def test_scan_single_token_each_time(self):
        assert Parser("(").scan_tokens()[0].token_type == TokenType.LEFT_PAREN
        assert Parser(")").scan_tokens()[0].token_type == TokenType.RIGHT_PAREN
        assert Parser("{").scan_tokens()[0].token_type == TokenType.LEFT_BRACE
        assert Parser("}").scan_tokens()[0].token_type == TokenType.RIGHT_BRACE
        assert Parser(",").scan_tokens()[0].token_type == TokenType.COMMA
        assert Parser(".").scan_tokens()[0].token_type == TokenType.DOT
        assert Parser("-").scan_tokens()[0].token_type == TokenType.MINUS
        assert Parser("+").scan_tokens()[0].token_type == TokenType.PLUS
        assert Parser(";").scan_tokens()[0].token_type == TokenType.SEMICOLON
        assert Parser("*").scan_tokens()[0].token_type == TokenType.STAR
        assert Parser("/").scan_tokens()[0].token_type == TokenType.SLASH


    def test_scan_double_token_each_time(self):
        assert Parser("!").scan_tokens()[0].token_type == TokenType.BANG
        assert Parser("!=").scan_tokens()[0].token_type == TokenType.BANG_EQUAL
        assert Parser("=").scan_tokens()[0].token_type == TokenType.EQUAL
        assert Parser("==").scan_tokens()[0].token_type == TokenType.EQUAL_EQUAL
        assert Parser(">").scan_tokens()[0].token_type == TokenType.GREATER
        assert Parser(">=").scan_tokens()[0].token_type == TokenType.GREATER_EQUAL
        assert Parser("<").scan_tokens()[0].token_type == TokenType.LESS
        assert Parser("<=").scan_tokens()[0].token_type == TokenType.LESS_EQUAL

    def test_scan_empty_tokens(self):
        assert len(Parser(" ").scan_tokens()) == 0
        assert len(Parser("\t").scan_tokens()) == 0
        assert len(Parser("\n").scan_tokens()) == 0
        assert len(Parser("\r").scan_tokens()) == 0

    def test_scan_comment_tokens(self):
        assert len(Parser("//").scan_tokens()) == 0
        assert len(Parser("//?as7ufoasdksadfk\n").scan_tokens()) == 0
        assert Parser("(//?as7ufoasdksadfk\n").scan_tokens()[0].token_type == TokenType.LEFT_PAREN

    def test_scan_single_char_tokens(self):
        source = "(){},.-+;*"
        parser = Parser(source)
        tokens = parser.scan_tokens()

        assert len(tokens) == 10
        assert tokens[0].token_type == TokenType.LEFT_PAREN
        assert tokens[1].token_type == TokenType.RIGHT_PAREN
        assert tokens[2].token_type == TokenType.LEFT_BRACE
        assert tokens[3].token_type == TokenType.RIGHT_BRACE
        assert tokens[4].token_type == TokenType.COMMA
        assert tokens[5].token_type == TokenType.DOT
        assert tokens[6].token_type == TokenType.MINUS
        assert tokens[7].token_type == TokenType.PLUS
        assert tokens[8].token_type == TokenType.SEMICOLON
        assert tokens[9].token_type == TokenType.STAR

    def test_scan_string_tokens(self):
        assert Parser('"abc"').scan_tokens()[0].token_type == TokenType.STRING
        assert Parser('"abc"').scan_tokens()[0].lexeme == "abc"
