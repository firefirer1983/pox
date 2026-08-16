from pox.resolver import Resolver
import time
from typing import cast
import pytest
from pox.token import Token, TokenType
from pox.callables import PoxFunction, PoxClass, PoxInstance
from pox.base import RunError
from pox.interpreter import Interpreter
from pox.parser import Parser
from pox.scanner import Scanner
from pox.statement import Stmt


def _parse(src: str):
    return Parser(Scanner(src).scan_tokens()).parse()


class TestInterpretExpr:
    def test_parse_literal_expr(self):
        assert Interpreter().visit(Parser(Scanner("5").scan_tokens()).expression(), ) == 5
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
        interpreter.visit_many(stmts)
        assert interpreter.global_env.get(token_a) == None

    def test_print_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("print 'hello';").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 1
        interpreter.visit(stmts[0])

    def test_var_declaration_with_initializer(self):
        interpreter = Interpreter()
        interpreter.visit_many(Parser(Scanner("var a = 5;").scan_tokens()).parse())
        assert interpreter.global_env.get(token_a) == 5

    def test_var_mix_statements(self):
        interpreter = Interpreter()
        tokens = Scanner("var a;a=5;a=a*3;").scan_tokens()
        stmts = Parser(tokens).parse()
        interpreter.visit(stmts[0])
        assert interpreter.global_env.get(token_a) == None
        interpreter.visit(stmts[1])
        assert interpreter.global_env.get(token_a) == 5
        interpreter.visit(stmts[2])
        assert interpreter.global_env.get(token_a) == 15

    def test_block_1_statement(self):
        interpreter = Interpreter()
        stmts = Parser(Scanner("var a;{a=5;}").scan_tokens()).parse()
        interpreter.visit(stmts[0])
        assert interpreter.global_env.get(token_a) == None
        interpreter.visit(stmts[1])
        assert interpreter.global_env.get(token_a) == 5

    def test_block_multi_statement(self):
        interpreter = Interpreter()
        stmts = Parser(Scanner("var a;{a=5;a=a*3;}").scan_tokens()).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        assert interpreter.global_env.get(token_a) == None
        interpreter.visit(stmts[1])
        assert interpreter.global_env.get(token_a) == 15

    def test_nested_block(self):
        interpreter = Interpreter()
        tokens = Scanner("var a=5;{a=3;{a=2;}}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        assert interpreter.global_env.get(token_a) == 5
        interpreter.visit(stmts[1])
        assert interpreter.global_env.get(token_a) == 2

    def test_if_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("var a=1;if (true){a=3;}else{a=4;}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        interpreter.visit(stmts[1])
        assert interpreter.global_env.get(token_a) == 3

    def test_else_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("var a=1;if (false){a=3;}else{a=4;}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        interpreter.visit(stmts[1])
        assert interpreter.global_env.get(token_a) == 4

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
        assert interpreter.global_env.get(token_a) == True

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
        result = cast(float, interpreter.visit(stmts[0]))
        assert int(result) == int(time.time())

    def test_func_def_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("fun test(a, b, c){return 0;}").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 1
        interpreter.visit(stmts[0])
        testfunc = cast(PoxFunction, interpreter.global_env.get(token_test))
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
        interpreter.with_resolve(stmts)
        interpreter.visit(stmts[0])
        assert interpreter.visit(stmts[1]) == 6

    def test_func_def_and_call_statement(self):
        interpreter = Interpreter()
        tokens = Scanner("fun test(){return 0;}test();").scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.with_resolve(stmts)
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
        interpreter.with_resolve(stmts)
        interpreter.visit(stmts[0])
        assert interpreter.visit(stmts[1]) == 55

    def test_fun_call_closure_statement(self):
        src = """
        fun makeCounter(){
          var i = 0;
          fun count(){
            i = i + 1;
          }
          return count;
        }
        makeCounter()();
        """
        interpreter = Interpreter()
        tokens = Scanner(src).scan_tokens()
        stmts = Parser(tokens).parse()
        assert len(stmts) == 2
        interpreter.with_resolve(stmts)
        interpreter.visit(stmts[0])
        interpreter.visit(stmts[1])
        # interpreter.visit(stmts[2])

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
        stmts = _parse(src)
        assert len(stmts) == 2
        interpreter.with_resolve(stmts)
        interpreter.visit(stmts[0])
        interpreter.visit(stmts[1])


token_foo = Token("Foo", TokenType.IDENTIFIER, "Foo", 0)
token_f = Token("f", TokenType.IDENTIFIER, "f", 0)
token_b = Token("b", TokenType.IDENTIFIER, "b", 0)


class TestInterpretClass:
    def test_class_definition(self):
        interpreter = Interpreter()
        stmts = _parse("class Foo{}")
        assert len(stmts) == 1
        interpreter.visit(stmts[0])
        klass = cast(PoxClass, interpreter.global_env.get(token_foo))
        assert isinstance(klass, PoxClass)
        assert klass.name.lexeme == "Foo"
        assert klass.methods == {}
        assert klass.arity() == 0
        assert klass.to_str() == "Class Foo"

    def test_class_definition_with_methods(self):
        interpreter = Interpreter()
        stmts = _parse("class Foo{init(a, b){}get(){}}")
        assert len(stmts) == 1
        interpreter.visit(stmts[0])
        klass = cast(PoxClass, interpreter.global_env.get(token_foo))
        assert set(klass.methods.keys()) == {"init", "get"}
        assert klass.find_method("init").arity() == 2
        assert klass.find_method("get").arity() == 0
        # 没有 init 时 arity 为 0，有 init 时为 init 的形参数
        assert klass.arity() == 2

    def test_class_instantiation(self):
        interpreter = Interpreter()
        stmts = _parse("class Foo{}var a = Foo();")
        assert len(stmts) == 2
        interpreter.visit(stmts[0])
        interpreter.visit(stmts[1])
        instance = cast(PoxInstance, interpreter.global_env.get(token_a))
        assert isinstance(instance, PoxInstance)
        assert instance.klass.name.lexeme == "Foo"
        assert instance.fields == {}

    def test_init_sets_fields(self):
        interpreter = Interpreter()
        src = """
        class Foo{
          init(a){
            this.a = a;
          }
        }
        var f = Foo(5);
        """
        stmts = _parse(src)
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts)
        instance = cast(PoxInstance, interpreter.global_env.get(token_f))
        assert instance.fields == {"a": 5}

    def test_init_with_bare_return(self):
        interpreter = Interpreter()
        src = """
        class Foo{
          init(){
            this.x = 1;
            return;
          }
        }
        var f = Foo();
        """
        stmts = _parse(src)
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts)
        instance = cast(PoxInstance, interpreter.global_env.get(token_f))
        assert instance.fields == {"x": 1}

    def test_instance_property_set_and_get(self):
        interpreter = Interpreter()
        src = """
        class Foo{}
        var a = Foo();
        a.x = 5;
        a.x;
        """
        stmts = _parse(src)
        assert len(stmts) == 4
        interpreter.visit_many(stmts)
        instance = cast(PoxInstance, interpreter.global_env.get(token_a))
        assert instance.get("x") == 5
        assert interpreter.visit(stmts[3]) == 5

    def test_instance_property_modify(self):
        interpreter = Interpreter()
        src = """
        class Foo{}
        var a = Foo();
        a.x = 1;
        a.x = a.x + 2;
        a.x = a.x * 3;
        """
        stmts = _parse(src)
        interpreter.visit_many(stmts)
        instance = cast(PoxInstance, interpreter.global_env.get(token_a))
        assert instance.get("x") == 9

    def test_method_call(self):
        interpreter = Interpreter()
        src = """
        class Foo{
          method(){
            return 42;
          }
        }
        var f = Foo();
        f.method();
        """
        stmts = _parse(src)
        assert len(stmts) == 3
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts[:2])
        assert interpreter.visit(stmts[2]) == 42

    def test_method_call_with_params(self):
        interpreter = Interpreter()
        src = """
        class Foo{
          add(a, b){
            return a + b;
          }
        }
        var f = Foo();
        f.add(2, 3);
        """
        stmts = _parse(src)
        assert len(stmts) == 3
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts[:2])
        assert interpreter.visit(stmts[2]) == 5

    def test_method_call_on_new_instance_expr(self):
        interpreter = Interpreter()
        src = """
        class Foo{
          method(){
            return 7;
          }
        }
        Foo().method();
        """
        stmts = _parse(src)
        assert len(stmts) == 2
        interpreter.with_resolve(stmts)
        interpreter.visit(stmts[0])
        assert interpreter.visit(stmts[1]) == 7

    def test_method_read_this_field(self):
        interpreter = Interpreter()
        src = """
        class Foo{
          init(){
            this.x = 10;
          }
          get(){
            return this.x;
          }
        }
        var f = Foo();
        f.get();
        """
        stmts = _parse(src)
        assert len(stmts) == 3
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts[:2])
        assert interpreter.visit(stmts[2]) == 10

    def test_method_modify_this_field(self):
        interpreter = Interpreter()
        src = """
        class Counter{
          init(){
            this.count = 0;
          }
          inc(){
            this.count = this.count + 1;
            return this.count;
          }
        }
        var f = Counter();
        f.inc();
        """
        stmts = _parse(src)
        assert len(stmts) == 3
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts[:2])
        assert interpreter.visit(stmts[2]) == 1
        assert interpreter.visit(stmts[2]) == 2

    def test_this_call_other_method(self):
        interpreter = Interpreter()
        src = """
        class Foo{
          init(){
            this.x = 3;
          }
          double(n){
            return n * 2;
          }
          compute(){
            return this.double(this.x);
          }
        }
        var f = Foo();
        f.compute();
        """
        stmts = _parse(src)
        assert len(stmts) == 3
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts[:2])
        assert interpreter.visit(stmts[2]) == 6

    def test_instances_state_independent(self):
        interpreter = Interpreter()
        src = """
        class Foo{
          init(x){
            this.x = x;
          }
          get(){
            return this.x;
          }
        }
        var a = Foo(1);
        var b = Foo(2);
        a.y = 10;
        b.y = 20;
        a.get();
        b.get();
        """
        stmts = _parse(src)
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts)
        instance_a = cast(PoxInstance, interpreter.global_env.get(token_a))
        instance_b = cast(PoxInstance, interpreter.global_env.get(token_b))
        assert instance_a.get("x") == 1
        assert instance_b.get("x") == 2
        assert instance_a.get("y") == 10
        assert instance_b.get("y") == 20

    def test_missing_method_raises(self):
        interpreter = Interpreter()
        src = """
        class Foo{}
        var f = Foo();
        f.missing();
        """
        stmts = _parse(src)
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts[:2])
        with pytest.raises(RunError):
            interpreter.visit(stmts[2])

    def test_get_property_on_class_raises(self):
        interpreter = Interpreter()
        src = """
        class Foo{}
        var f = Foo;
        f.x;
        """
        stmts = _parse(src)
        interpreter.with_resolve(stmts)
        interpreter.visit_many(stmts[:2])
        with pytest.raises(RunError):
            interpreter.visit(stmts[2])

    def test_instantiate_with_wrong_arity_raises(self):
        interpreter = Interpreter()
        src = """
        class Foo{
          init(a, b){
            this.a = a;
            this.b = b;
          }
        }
        var f = Foo(1);
        """
        stmts = _parse(src)
        interpreter.with_resolve(stmts)
        interpreter.visit(stmts[0])
        with pytest.raises(RunError):
            interpreter.visit(stmts[1])
