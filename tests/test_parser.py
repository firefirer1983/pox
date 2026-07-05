from pox.interpreter import AstPrinter
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
        expr = Parser(Scanner("-1").scan_tokens()).expression()
        assert (
            AstPrinter().visit(expr) == "-1"
        )

        expr = Parser(Scanner("--1").scan_tokens()).expression()
        assert (
            AstPrinter().visit(expr) == "1"
        )

        expr = Parser(Scanner("---1").scan_tokens()).expression()
        assert (
            AstPrinter().visit(expr) == "-1"
        )

    def test_parse_binary_expr(self):
        assert (
            AstPrinter().visit(Parser(Scanner("5+1").scan_tokens()).expression())
            == "(5+1)"
        )
        assert (
            AstPrinter().visit(Parser(Scanner("5-1").scan_tokens()).expression())
            == "(5-1)"
        )
        assert (
            AstPrinter().visit(Parser(Scanner("5*1").scan_tokens()).expression())
            == "(5*1)"
        )
        assert (
            AstPrinter().visit(Parser(Scanner("5/1").scan_tokens()).expression())
            == "(5/1)"
        )

    def test_parse_mix_expr(self):
        assert (
            AstPrinter().visit(Parser(Scanner("5+1*6").scan_tokens()).expression())
            == "(5+(1*6))"
        )
        assert (
            AstPrinter().visit(Parser(Scanner("-2+5/4+1*6").scan_tokens()).expression())
            == "((-2+(5/4))+(1*6))"
        )

    def test_parse_var_expr(self):
        assert (
            AstPrinter().visit(Parser(Scanner("a + 1").scan_tokens()).expression())
            == "(a+1)"
        )

    def test_parse_assign_expr(self):
        assert (
            AstPrinter().visit(Parser(Scanner("a = 5").scan_tokens()).expression())
            == "a=5"
        )

    def test_parse_var_stmt(self):
        assert (
            AstPrinter().visit(
                Parser(Scanner("var a = 5;").scan_tokens()).declaration()
            )
            == "var a=5;"
        )

    def test_parse_block_stmt(self):
        tokens = Scanner("{var a = 5;}").scan_tokens()

        stmts = Parser(tokens).parse()
        assert len(stmts) == 1
        assert AstPrinter().visit(stmts[0]) == "{var a=5;}"

    def test_parse_if_stmt(self):
        tokens = Scanner("if (a>5) {a=3;}").scan_tokens()
        stmt = Parser(tokens).declaration()
        assert AstPrinter().visit(stmt) == "if ((a>5)){a=3;}"

    def test_parse_logical_expr(self):
        tokens = Scanner("true or false").scan_tokens()
        assert AstPrinter().visit(Parser(tokens).expression()) == "(True or False)"

        tokens = Scanner("a = false or true").scan_tokens()
        assert AstPrinter().visit(Parser(tokens).expression()) == "a=(False or True)"

        tokens = Scanner("a = true and true or a").scan_tokens()
        assert (
            AstPrinter().visit(Parser(tokens).expression())
            == "a=(True and (True or a))"
        )

    def test_parse_while_statement(self):
        tokens = Scanner("while(true){var a=5;}").scan_tokens()
        statment = Parser(tokens).statement()
        assert AstPrinter().visit(statment) == "while(True){var a=5;}"

    def test_parse_for_statement(self):
        tokens = Scanner("for(;a<10;){a=6;}").scan_tokens()
        statment = Parser(tokens).statement()
        assert AstPrinter().visit(statment) == "while((a<10)){a=6;}"

        tokens = Scanner("for(var a=0;a<10;){a=6;}").scan_tokens()
        statment = Parser(tokens).statement()
        assert AstPrinter().visit(statment) == "{var a=0;while((a<10)){a=6;}}"

        tokens = Scanner("for(var a=0;a<10;a=a+1){a=6;}").scan_tokens()
        statment = Parser(tokens).statement()
        assert AstPrinter().visit(statment) == "{var a=0;while((a<10)){a=6;a=(a+1);}}"

    def test_parse_func_call_expr(self):
        # tokens = Scanner("assert(0)").scan_tokens()
        # expr = Parser(tokens).call()
        # assert len(expr.arguments) == 1

        tokens = Scanner("assert(1,2,3)").scan_tokens()
        expr = Parser(tokens).call()
        assert len(expr.arguments) == 3

        tokens = Scanner("assert(0)('abc')(nil)(true)").scan_tokens()
        expr = Parser(tokens).call()
        assert len(expr.arguments) == 1

        tokens = Scanner("assert(0)('abc')(nil)(true, a, b)").scan_tokens()
        expr = Parser(tokens).call()
        assert len(expr.arguments) == 3
