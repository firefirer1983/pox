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
        assert (
            Parser("(//?as7ufoasdksadfk\n").scan_tokens()[0].token_type
            == TokenType.LEFT_PAREN
        )

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
        assert Parser('"abc def"').scan_tokens()[0].lexeme == "abc def"

    def test_scan_number_tokens(self):
        assert Parser("123").scan_tokens()[0].token_type == TokenType.NUMBER
        assert Parser("123").scan_tokens()[0].lexeme == "123"
        assert Parser("123.456").scan_tokens()[0].lexeme == "123.456"
        assert Parser("123 ").scan_tokens()[0].lexeme == "123"
        assert Parser("123 + 456 ").scan_tokens()[0].lexeme == "123"
        assert Parser("123 + 456 ").scan_tokens()[1].token_type == TokenType.PLUS
        assert Parser("123 + 456 ").scan_tokens()[2].lexeme == "456"

    def test_scan_identifier_tokens(self):
        assert Parser("abc").scan_tokens()[0].token_type == TokenType.IDENTIFIER
        assert Parser("abc").scan_tokens()[0].lexeme == "abc"
        assert Parser("_abc").scan_tokens()[0].token_type == TokenType.IDENTIFIER
        assert Parser("_abc").scan_tokens()[0].lexeme == "_abc"
        assert Parser("_abc123").scan_tokens()[0].token_type == TokenType.IDENTIFIER
        assert Parser("_abc123").scan_tokens()[0].lexeme == "_abc123"
        assert Parser("_123").scan_tokens()[0].token_type == TokenType.IDENTIFIER
        assert Parser("_123").scan_tokens()[0].lexeme == "_123"

    def test_scan_reserve_keyword_tokens(self):
        assert Parser("and").scan_tokens()[0].token_type == TokenType.AND
        assert Parser("class").scan_tokens()[0].token_type == TokenType.CLASS
        assert Parser("else").scan_tokens()[0].token_type == TokenType.ELSE
        assert Parser("false").scan_tokens()[0].token_type == TokenType.FALSE
        assert Parser("fun").scan_tokens()[0].token_type == TokenType.FUN
        assert Parser("for").scan_tokens()[0].token_type == TokenType.FOR
        assert Parser("if").scan_tokens()[0].token_type == TokenType.IF
        assert Parser("nil").scan_tokens()[0].token_type == TokenType.NIL
        assert Parser("or").scan_tokens()[0].token_type == TokenType.OR
        assert Parser("print").scan_tokens()[0].token_type == TokenType.PRINT
        assert Parser("return").scan_tokens()[0].token_type == TokenType.RETURN
        assert Parser("super").scan_tokens()[0].token_type == TokenType.SUPER
        assert Parser("this").scan_tokens()[0].token_type == TokenType.THIS
        assert Parser("true").scan_tokens()[0].token_type == TokenType.TRUE
        assert Parser("var").scan_tokens()[0].token_type == TokenType.VAR
        assert Parser("while").scan_tokens()[0].token_type == TokenType.WHILE
