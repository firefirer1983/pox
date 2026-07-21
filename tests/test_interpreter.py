import time
from typing import cast
from pox.token import Token, TokenType
from pox.callables import PoxFunction
from pox.environment import global_env
from pox.interpreter import Interpreter
from pox.parser import Parser
from pox.scanner import Scanner
from pox.statement import Stmt


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


token_a = Token("a", TokenType.STRING, "a", 0)
token_test = Token("test", TokenType.VAR, "test", 0)


class TestInterpretStmt:
    def test_unary_expr(self):
        interpreter = Interpreter()
        expr = Parser(Scanner("-1").scan_tokens()).expression()
        assert interpreter.visit(expr) == -1
        expr = Parser(Scanner("--1").scan_tokens()).expression()
        assert interpreter.visit(expr) == 1
        expr = Parser(Scanner("---1").scan_tokens()).expression()
        assert interpreter.visit(expr) == -1

    def test_var_declaration_without_initializer(self):
        interpreter = Interpreter()
        stmts = Parser(Scanner("var a;").scan_tokens()).parse()
        assert len(stmts) == 1
        interpreter.visit(stmts[0])
        assert global_env.get(token_a) == None

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
            assert global_env.get(token_a) == 5

    def test_var_mix_statements(self):
        interpreter = Interpreter()
        tokens = Scanner("var a;a=5;a=a*3;").scan_tokens()
        stmts = Parser(tokens).parse()
        interpreter.visit(stmts[0])
        assert global_env.get(token_a) == None
        interpreter.visit(stmts[1])
        assert global_env.get(token_a) == 5
        interpreter.visit(stmts[2])
        assert global_env.get(token_a) == 15

    def test_block_1_statement(self):
        interpreter = Interpreter()
        stmts = Parser(Scanner("var a;{a=5;}").scan_tokens()).parse()
        interpreter.visit(stmts[0])
        assert global_env.get(token_a) == None
        interpreter.visit(stmts[1])
        assert global_env.get(token_a) == 5

    def test_block_multi_statement(self):
        interpreter = Interpreter()
        stmts = Parser(Scanner("var a;{a=5;a=a*3;}").scan_tokens()).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        assert global_env.get(token_a) == None
        interpreter.visit(stmts[1])
        assert global_env.get(token_a) == 15

    def test_nested_block(self):
        interpreter = Interpreter()
        tokens = Scanner("var a=5;{a=3;{a=2;}}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        assert global_env.get(token_a) == 5
        interpreter.visit(stmts[1])
        assert global_env.get(token_a) == 2

    def test_if_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("var a=1;if (true){a=3;}else{a=4;}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        interpreter.visit(stmts[1])
        assert global_env.get(token_a) == 3

    def test_else_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("var a=1;if (false){a=3;}else{a=4;}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        interpreter.visit(stmts[1])
        assert global_env.get(token_a) == 4

    def test_logical_expr(self):
        interpreter = Interpreter()
        tokens = Scanner("true or false").scan_tokens()
        expr = Parser(tokens).expression()
        interpreter.visit(expr) == True

        tokens = Scanner("false or true").scan_tokens()
        expr = Parser(tokens).expression()
        interpreter.visit(expr) == True

        tokens = Scanner("false and true").scan_tokens()
        expr = Parser(tokens).expression()
        interpreter.visit(expr) == False

        tokens = Scanner("true and true").scan_tokens()
        expr = Parser(tokens).expression()
        interpreter.visit(expr) == True

        interpreter = Interpreter()
        tokens = Scanner("var a=false or true;").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 1
        interpreter.visit(stmts[0])
        assert global_env.get(token_a) == True

    def test_nested_or_expr(self):
        interpreter = Interpreter()
        tokens = Scanner("false or false or true or false").scan_tokens()
        expr = Parser(tokens).expression()
        assert interpreter.visit(expr) == True

    def test_nested_and_expr(self):
        interpreter = Interpreter()
        tokens = Scanner("true and true and false").scan_tokens()
        expr = Parser(tokens).expression()
        assert interpreter.visit(expr) == False

    def test_print_and_logical_expr(self):
        interpreter = Interpreter()
        tokens = Scanner("print false or 'hello world';").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 1
        interpreter.visit(stmts[0])

    def test_func_call_expr(self):
        interpreter = Interpreter()
        tokens = Scanner("time();").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 1
        result = cast(float, interpreter.visit(stmts[0], global_env))
        assert int(result) == int(time.time())

    def test_func_def_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("fun test(a, b, c){return 0;}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 1
        interpreter.visit(stmts[0])
        testfunc = cast(PoxFunction, global_env.get(token_test))
        assert testfunc.arity() == 3
        assert testfunc.parameters[0].lexeme == "a"
        assert testfunc.parameters[1].lexeme == "b"
        assert testfunc.parameters[2].lexeme == "c"
        assert len(testfunc.block.statements) == 1
        ret_stmt = cast(Stmt.Return, testfunc.block.statements[0])
        assert interpreter.visit(ret_stmt.value) == 0

    def test_func_def_params_statements(self):
        interpreter = Interpreter()
        tokens = Scanner("fun test(a, b){return a*b;}test(2,3);").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        assert interpreter.visit(stmts[1]) == 6

    def test_func_def_and_call_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("fun test(){return 0;}test();").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        assert interpreter.visit(stmts[1]) == 0

    def test_recursive_fun_call_statement(self):
        interpreter = Interpreter()
        src = """
        fun fib(n){
          if (n <= 1)
            return n;
          return fib(n-2) + fib(n-1);
        }
        fib(10);
        """
        tokens = Scanner(src).scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        assert interpreter.visit(stmts[1]) == 55

    def test_nested_fun_call_statement(self):
        src = """
        fun makeCounter(){
          var i = 0;
          fun count(){
            i = i + 1;
            print(i);
          }
          return count;
        }
        var f = makeCounter();
        f();
        """
        interpreter = Interpreter()
        tokens = Scanner(src).scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 3
        interpreter.visit(stmts[0])
        interpreter.visit(stmts[1])
        interpreter.visit(stmts[2])

    def test_nested_fun_multi_call_statement(self):
        src = """
        var a = "global";
        {
          fun showA() {
            print a;
          }

          showA();
          var a = "block";
          showA();
        }
        """
        interpreter = Interpreter()
        tokens = Scanner(src).scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        interpreter.visit(stmts[1])
