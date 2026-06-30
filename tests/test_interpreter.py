from pox.environment import global_env
from pox.interpreter import Interpreter
from pox.parser import Parser
from pox.scanner import Scanner


class TestInterpretExpr:
    def test_parse_literal_expr(self):
        assert Interpreter().visit(Parser(Scanner("5").scan_tokens()).expression()) == 5
        assert (
            Interpreter().visit(Parser(Scanner('"abc"').scan_tokens()).expression())
            == "abc"
        )

    def test_parse_unary_expr(self):
        assert (
            Interpreter().visit(Parser(Scanner("-1").scan_tokens()).expression()) == -1
        )

    def test_parse_binary_expr(self):
        assert (
            Interpreter().visit(Parser(Scanner("5+1").scan_tokens()).expression()) == 6
        )
        assert (
            Interpreter().visit(Parser(Scanner("5-1").scan_tokens()).expression()) == 4
        )
        assert (
            Interpreter().visit(Parser(Scanner("5*1").scan_tokens()).expression()) == 5
        )
        assert (
            Interpreter().visit(Parser(Scanner("5/1").scan_tokens()).expression()) == 5
        )

    def test_parse_mix_expr(self):
        assert (
            Interpreter().visit(Parser(Scanner("5+1*6").scan_tokens()).expression())
            == 11
        )
        assert (
            Interpreter().visit(
                Parser(Scanner("-2+5/4+1*6").scan_tokens()).expression()
            )
            == 5.25
        )


class TestInterpretStmt:
    def test_var_declaration_without_initializer(self):
        interpreter = Interpreter()
        stmts = Parser(Scanner("var a;").scan_tokens()).parse()
        assert len(stmts) == 1
        interpreter.visit(stmts[0])
        assert global_env.get("a") == None

    def test_print_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("print 'hello';").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 1
        interpreter.visit(stmts[0])

    def test_var_declaration_with_initializer(self):
        interpreter = Interpreter()
        for stmt in Parser(Scanner("var a = 5;").scan_tokens()).parse():
            interpreter.visit(stmt)
            assert global_env.get("a") == 5

    def test_var_mix_statements(self):
        interpreter = Interpreter()
        tokens = Scanner("var a;a=5;a=a*3;").scan_tokens()
        stmts = Parser(tokens).parse()
        interpreter.visit(stmts[0])
        assert global_env.get("a") == None
        interpreter.visit(stmts[1])
        assert global_env.get("a") == 5
        interpreter.visit(stmts[2])
        assert global_env.get("a") == 15

    def test_block_1_statement(self):
        interpreter = Interpreter()
        stmts = Parser(Scanner("var a;{a=5;}").scan_tokens()).parse()
        interpreter.visit(stmts[0])
        assert global_env.get("a") == None
        interpreter.visit(stmts[1])
        assert global_env.get("a") == 5

    def test_block_multi_statement(self):
        interpreter = Interpreter()
        stmts = Parser(Scanner("var a;{a=5;a=a*3;}").scan_tokens()).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        assert global_env.get("a") == None
        interpreter.visit(stmts[1])
        assert global_env.get("a") == 15

    def test_nested_block(self):
        interpreter = Interpreter()
        tokens = Scanner("var a=5;{a=3;{a=2;}}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts)== 2
        interpreter.visit(stmts[0])
        assert global_env.get("a") == 5
        interpreter.visit(stmts[1])
        assert global_env.get("a") == 2
