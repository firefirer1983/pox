from pox.interpreter import Interpreter, AstPrinter
from pox.scanner import Scanner
from pox.parser import Parser


class TestAstPrinter:
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

    def test_parse_var_expr(self):
        assert AstPrinter().visit(Parser(Scanner("a + 1").scan_tokens()).expression()) == "(+ a 1)"

    def test_parse_assign_expr(self):
        assert AstPrinter().visit(Parser(Scanner("a = 5").scan_tokens()).expression()) == "a=5"

    def test_parse_var_stmt(self):
        assert AstPrinter().visit(Parser(Scanner("var a = 5;").scan_tokens()).declaration()) == "var a=5;"

    def test_parse_block_stmt(self):
        tokens = Scanner("{var a = 5;}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 1
        assert AstPrinter().visit(stmts[0]) == "var a=5;"
