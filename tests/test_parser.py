from pox.parser import AstPrinter
from pox.token import TokenType
from pox.scanner import Scanner
from pox.parser import Parser


class TestParseExpression:
    def test_parse_literal_expr(self):
        assert (
            AstPrinter().visit(Parser(Scanner("5").scan_tokens()).expression()) == "5"
        )
        assert (
            AstPrinter().visit(Parser(Scanner('"abc"').scan_tokens()).expression())
            == "abc"
        )

    def test_parse_unary_expr(self):
        assert (
            AstPrinter().visit(Parser(Scanner("-1").scan_tokens()).expression()) == "-1"
        )

    def test_parse_binary_expr(self):
        assert (
            AstPrinter().visit(Parser(Scanner("5+1").scan_tokens()).expression())
            == "(+ 5 1)"
        )
        assert (
            AstPrinter().visit(Parser(Scanner("5-1").scan_tokens()).expression())
            == "(- 5 1)"
        )
        assert (
            AstPrinter().visit(Parser(Scanner("5*1").scan_tokens()).expression())
            == "(* 5 1)"
        )
        assert (
            AstPrinter().visit(Parser(Scanner("5/1").scan_tokens()).expression())
            == "(/ 5 1)"
        )


    def test_parse_mix_expr(self):
        assert (
            AstPrinter().visit(Parser(Scanner("5+1*6").scan_tokens()).expression())
            == "(+ 5 (* 1 6))"
        )
        assert (
            AstPrinter().visit(Parser(Scanner("-2+5/4+1*6").scan_tokens()).expression())
            == "(+ (+ -2 (/ 5 4)) (* 1 6))"
        )
