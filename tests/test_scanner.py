from pox.scanner import Scanner
from pox.token import TokenType


class TestScanSingleToken:
    def test_scan_single_token_each_time(self):
        assert Scanner("(").scan_tokens()[0].token_type == TokenType.LEFT_PAREN
        assert Scanner(")").scan_tokens()[0].token_type == TokenType.RIGHT_PAREN
        assert Scanner("{").scan_tokens()[0].token_type == TokenType.LEFT_BRACE
        assert Scanner("}").scan_tokens()[0].token_type == TokenType.RIGHT_BRACE
        assert Scanner(",").scan_tokens()[0].token_type == TokenType.COMMA
        assert Scanner(".").scan_tokens()[0].token_type == TokenType.DOT
        assert Scanner("-").scan_tokens()[0].token_type == TokenType.MINUS
        assert Scanner("+").scan_tokens()[0].token_type == TokenType.PLUS
        assert Scanner(";").scan_tokens()[0].token_type == TokenType.SEMICOLON
        assert Scanner("*").scan_tokens()[0].token_type == TokenType.STAR
        assert Scanner("/").scan_tokens()[0].token_type == TokenType.SLASH

    def test_scan_double_token_each_time(self):
        assert Scanner("!").scan_tokens()[0].token_type == TokenType.BANG
        assert Scanner("!=").scan_tokens()[0].token_type == TokenType.BANG_EQUAL
        assert Scanner("=").scan_tokens()[0].token_type == TokenType.EQUAL
        assert Scanner("==").scan_tokens()[0].token_type == TokenType.EQUAL_EQUAL
        assert Scanner(">").scan_tokens()[0].token_type == TokenType.GREATER
        assert Scanner(">=").scan_tokens()[0].token_type == TokenType.GREATER_EQUAL
        assert Scanner("<").scan_tokens()[0].token_type == TokenType.LESS
        assert Scanner("<=").scan_tokens()[0].token_type == TokenType.LESS_EQUAL

    def test_scan_empty_tokens(self):
        assert len(Scanner(" ").scan_tokens()) == 0
        assert len(Scanner("\t").scan_tokens()) == 0
        assert len(Scanner("\n").scan_tokens()) == 0
        assert len(Scanner("\r").scan_tokens()) == 0

    def test_scan_comment_tokens(self):
        assert len(Scanner("//").scan_tokens()) == 0
        assert len(Scanner("//?as7ufoasdksadfk\n").scan_tokens()) == 0
        assert (
            Scanner("(//?as7ufoasdksadfk\n").scan_tokens()[0].token_type
            == TokenType.LEFT_PAREN
        )

    def test_scan_single_char_tokens(self):
        source = "(){},.-+;*"
        parser = Scanner(source)
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
        assert Scanner('"abc"').scan_tokens()[0].token_type == TokenType.STRING
        assert Scanner('"abc"').scan_tokens()[0].lexeme == "abc"
        assert Scanner('"abc def"').scan_tokens()[0].lexeme == "abc def"

    def test_scan_number_tokens(self):
        assert Scanner("123").scan_tokens()[0].token_type == TokenType.NUMBER
        assert Scanner("123").scan_tokens()[0].lexeme == "123"
        assert Scanner("123.456").scan_tokens()[0].lexeme == "123.456"
        assert Scanner("123 ").scan_tokens()[0].lexeme == "123"
        assert Scanner("123 + 456 ").scan_tokens()[0].lexeme == "123"
        assert Scanner("123 + 456 ").scan_tokens()[1].token_type == TokenType.PLUS
        assert Scanner("123 + 456 ").scan_tokens()[2].lexeme == "456"

    def test_scan_identifier_tokens(self):
        assert Scanner("abc").scan_tokens()[0].token_type == TokenType.IDENTIFIER
        assert Scanner("abc").scan_tokens()[0].lexeme == "abc"
        assert Scanner("_abc").scan_tokens()[0].token_type == TokenType.IDENTIFIER
        assert Scanner("_abc").scan_tokens()[0].lexeme == "_abc"
        assert Scanner("_abc123").scan_tokens()[0].token_type == TokenType.IDENTIFIER
        assert Scanner("_abc123").scan_tokens()[0].lexeme == "_abc123"
        assert Scanner("_123").scan_tokens()[0].token_type == TokenType.IDENTIFIER
        assert Scanner("_123").scan_tokens()[0].lexeme == "_123"

    def test_scan_reserve_keyword_tokens(self):
        assert Scanner("and").scan_tokens()[0].token_type == TokenType.AND
        assert Scanner("class").scan_tokens()[0].token_type == TokenType.CLASS
        assert Scanner("else").scan_tokens()[0].token_type == TokenType.ELSE
        assert Scanner("false").scan_tokens()[0].token_type == TokenType.FALSE
        assert Scanner("fun").scan_tokens()[0].token_type == TokenType.FUN
        assert Scanner("for").scan_tokens()[0].token_type == TokenType.FOR
        assert Scanner("if").scan_tokens()[0].token_type == TokenType.IF
        assert Scanner("nil").scan_tokens()[0].token_type == TokenType.NIL
        assert Scanner("or").scan_tokens()[0].token_type == TokenType.OR
        assert Scanner("print").scan_tokens()[0].token_type == TokenType.PRINT
        assert Scanner("return").scan_tokens()[0].token_type == TokenType.RETURN
        assert Scanner("super").scan_tokens()[0].token_type == TokenType.SUPER
        assert Scanner("this").scan_tokens()[0].token_type == TokenType.THIS
        assert Scanner("true").scan_tokens()[0].token_type == TokenType.TRUE
        assert Scanner("var").scan_tokens()[0].token_type == TokenType.VAR
        assert Scanner("while").scan_tokens()[0].token_type == TokenType.WHILE


    def test_scan_mix_var_tokens(self):
        tokens = Scanner("var a = 3").scan_tokens()
        assert len(tokens) == 4
        assert tokens[0].token_type == TokenType.VAR
        assert tokens[1].token_type == TokenType.IDENTIFIER
        assert tokens[2].token_type == TokenType.EQUAL
        assert tokens[3].token_type == TokenType.NUMBER
