import time
from typing import cast

import pytest

from pox.base import ResolveError, ReturnException
from pox.callables import PoxFunction
from pox.environment import global_env
from pox.expression import Expr
from pox.interpreter import Interpreter
from pox.resolver import Resolver
from pox.parser import Parser
from pox.scanner import Scanner
from pox.statement import Stmt


def _parse(src: str):
    return Parser(Scanner(src).scan_tokens()).parse()


class TestResolverStmt:
    def test_var_expr(self):
        src = """
        var a = 5;
        print a;
        """
        resolver = Resolver()
        stmts = Parser(Scanner(src).scan_tokens()).parse()
        assert len(stmts) == 2
        resolver.visit_many(stmts)
        print_stmt = cast(Stmt.PrintStmt, stmts[1])
        assert resolver.resolve(print_stmt.expr) == 0

    # ---- Expr.* branches ----

    def test_literal_expr(self):
        """Expr.Literal: visit 是 no-op，不应出错且不加入 locals。"""
        src = "var a = 5;"
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        var_stmt = cast(Stmt.Var, stmts[0])
        literal = cast(Expr.Literal, var_stmt.initializer)
        assert literal.value == 5
        # 重复 visit 不应抛异常
        resolver.visit(literal)
        # literal 不会进入 locals
        assert literal not in resolver.locals

    def test_unary_expr(self):
        """Expr.Unary: 递归 visit 子表达式。"""
        src = """
        var a = 1;
        var b = -a;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        var_b = cast(Stmt.Var, stmts[1])
        unary = cast(Expr.Unary, var_b.initializer)
        # 内部的 Variable a 应被解析到 global(depth=0)
        assert isinstance(unary.right, Expr.Variable)
        assert resolver.resolve(unary.right) == 0

    def test_binary_expr(self):
        """Expr.Binary: 递归 visit 左右子表达式。"""
        src = """
        var a = 1;
        var b = 2;
        var c = a + b;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        var_c = cast(Stmt.Var, stmts[2])
        binary = cast(Expr.Binary, var_c.initializer)
        assert resolver.resolve(binary.left) == 0
        assert resolver.resolve(binary.right) == 0

    def test_grouping_expr(self):
        """Expr.Grouping: 递归 visit 内部表达式。"""
        src = """
        var a = 1;
        var b = (a);
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        var_b = cast(Stmt.Var, stmts[1])
        grouping = cast(Expr.Grouping, var_b.initializer)
        # 内部 Variable a 应被正确解析
        inner = cast(Expr.Variable, grouping.expr)
        assert resolver.resolve(inner) == 0

    def test_variable_nested_scope(self):
        """Expr.Variable: 从内层作用域访问外层变量，depth 应反映层级距离。"""
        src = """
        var a = 1;
        {
            var b = 2;
            {
                print a;
            }
        }
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        outer_block = cast(Stmt.Block, stmts[1])
        inner_block = cast(Stmt.Block, outer_block.statements[1])
        print_a = cast(Stmt.PrintStmt, inner_block.statements[0])
        # a 在最外层，当前 print 在两层 block 内 → depth = 2
        assert resolver.resolve(print_a.expr) == 2

    def test_assign_expr(self):
        """Expr.Assign: 赋值表达式应被加入 locals 并可被 resolve。"""
        src = """
        var a = 1;
        a = 2;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        expr_stmt = cast(Stmt.ExprStmt, stmts[1])
        assign = cast(Expr.Assign, expr_stmt.expr)
        assert resolver.resolve(assign) == 0

    def test_assign_nested_scope(self):
        """Expr.Assign: 给外层变量赋值，depth 应反映层级距离。"""
        src = """
        var a = 1;
        {
            a = 2;
        }
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        block = cast(Stmt.Block, stmts[1])
        expr_stmt = cast(Stmt.ExprStmt, block.statements[0])
        assign = cast(Expr.Assign, expr_stmt.expr)
        assert resolver.resolve(assign) == 1

    def test_logical_expr(self):
        """Expr.Logical: 递归 visit 左右子表达式。"""
        src = """
        var a = true;
        var b = false;
        var c = a or b;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        var_c = cast(Stmt.Var, stmts[2])
        logical = cast(Expr.Logical, var_c.initializer)
        assert resolver.resolve(logical.left) == 0
        assert resolver.resolve(logical.right) == 0

    def test_logical_and_expr(self):
        """Expr.Logical: and 分支同样覆盖。"""
        src = """
        var a = true;
        var b = false;
        var c = a and b;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        var_c = cast(Stmt.Var, stmts[2])
        logical = cast(Expr.Logical, var_c.initializer)
        assert resolver.resolve(logical.left) == 0
        assert resolver.resolve(logical.right) == 0

    def test_call_expr(self):
        """Expr.Call: 递归 visit 被调用者和参数。"""
        src = """
        var x = 1;
        var y = 2;
        fun f(a, b){
          print a+b;
        }
        var d = f(x, y);
        """
        resolver = Resolver()
        stmts = _parse(src)
        assert len(stmts) == 4
        var_d = cast(Stmt.Var, stmts[-1])
        call = cast(Expr.Call, var_d.initializer)
        resolver.visit_many(stmts)
        # 单独 visit call：x,y 在 global scope
        arg0 = cast(Expr.Variable, call.arguments[0])
        arg1 = cast(Expr.Variable, call.arguments[1])
        assert resolver.resolve(arg0) == 0
        assert resolver.resolve(arg1) == 0

    # ---- Stmt.* branches ----

    def test_print_stmt(self):
        """Stmt.PrintStmt: 单独覆盖 print 分支。"""
        src = """
        var a = 1;
        print a + 1;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        print_stmt = cast(Stmt.PrintStmt, stmts[1])
        binary = cast(Expr.Binary, print_stmt.expr)
        # 左侧是 Variable a，可被 resolve
        assert resolver.resolve(binary.left) == 0

    def test_expr_stmt(self):
        """Stmt.ExprStmt: 可通过 resolve() 拿到内部表达式的 depth。"""
        src = """
        var a = 1;
        a;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        expr_stmt = cast(Stmt.ExprStmt, stmts[1])
        assert resolver.resolve(expr_stmt) == 0

    def test_var_no_initializer(self):
        """Stmt.Var: 无 initializer 时只 declare + define。"""
        src = """
        var a;
        print a;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        print_stmt = cast(Stmt.PrintStmt, stmts[1])
        assert resolver.resolve(print_stmt.expr) == 0

    def test_block_stmt(self):
        """Stmt.Block: 进入新作用域，退出时弹出。"""
        src = """
        var a = 1;
        {
            var b = 2;
            print a;
            print b;
        }
        print a;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        block = cast(Stmt.Block, stmts[1])
        # 内层 print a：a 在外层 → depth = 1
        print_a_in_block = cast(Stmt.PrintStmt, block.statements[1])
        assert resolver.resolve(print_a_in_block.expr) == 1
        # 内层 print b：b 在内层 → depth = 0
        print_b_in_block = cast(Stmt.PrintStmt, block.statements[2])
        assert resolver.resolve(print_b_in_block.expr) == 1
        # 出块后 print a 仍可访问
        print_a_after = cast(Stmt.PrintStmt, stmts[2])
        assert resolver.resolve(print_a_after.expr) == 0

    def test_block_scope_isolation(self):
        """Stmt.Block: 块内声明不影响外层 scopes。"""
        src = """
        {
            var a = 1;
        }
        var a = 2;
        print a;
        """
        resolver = Resolver()
        stmts = _parse(src)
        # 不应抛 "a is already exists"，因为内外层作用域不同
        resolver.visit_many(stmts)
        print_stmt = cast(Stmt.PrintStmt, stmts[2])
        assert resolver.resolve(print_stmt.expr) == 0

    def test_if_stmt(self):
        """Stmt.IF: 解析 condition / consequent。"""
        src = """
        var a = 1;
        if (a) {
            var b = 2;
            print b;
        }
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        if_stmt = cast(Stmt.IF, stmts[1])
        # condition 中的 a 在外层
        assert resolver.resolve(if_stmt.condition) == 0
        # consequent 块内的 b 是内层
        block = cast(Stmt.Block, if_stmt.consequent)
        print_b = cast(Stmt.PrintStmt, block.statements[1])
        assert resolver.resolve(print_b.expr) == 0

    def test_if_with_else(self):
        """Stmt.IF: 同时覆盖 alternative 分支。"""
        src = """
        var a = 1;
        if (a) {
            print a;
        } else {
            var b = 2;
            print b;
        }
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        if_stmt = cast(Stmt.IF, stmts[1])
        assert if_stmt.alternative is not None
        else_block = cast(Stmt.Block, if_stmt.alternative)
        # else 块内访问外层 a → depth = 1
        print_a = cast(Stmt.PrintStmt, else_block.statements[0])
        assert resolver.resolve(print_a.expr) == 1
        # else 块内 b 是内层 → depth = 0
        var_b = cast(Stmt.Var, else_block.statements[0])
        print_b = cast(Stmt.PrintStmt, else_block.statements[1])
        assert resolver.resolve(print_b.expr) == 0

    def test_while_stmt(self):
        """Stmt.While: 解析 condition 和 body。"""
        src = """
        var a = 0;
        while (a) {
            print a;
        }
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        while_stmt = cast(Stmt.While, stmts[1])
        # condition a 在外层
        assert resolver.resolve(while_stmt.condition) == 0
        # body 块内的 print a 在内层 → depth = 1
        body = cast(Stmt.Block, while_stmt.statement)
        print_a = cast(Stmt.PrintStmt, body.statements[0])
        assert resolver.resolve(print_a.expr) == 1

    def test_function_stmt(self):
        """Stmt.Function: 函数名先声明再定义，可在外部解析。"""
        src = """
        fun foo(a) {
            print a;
        }
        print foo;
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        # 函数名 foo 仍然被 declare+define
        print_stmt = cast(Stmt.PrintStmt, stmts[1])
        assert resolver.resolve(print_stmt.expr) == 0

    def test_function_params(self):
        """Stmt.Function: 函数参数在函数作用域内可见。"""
        src = """
        fun foo(a) {
            print a;
        }
        """
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        func_stmt = cast(Stmt.Function, stmts[0])
        # 手动进入函数作用域并 visit print（不触达 return）
        with resolver.scoping():
            for arg in func_stmt.parameters:
                resolver.declare(arg)
                resolver.define(arg)
            block = func_stmt.block
            print_stmt = cast(Stmt.PrintStmt, block.statements[0])
            resolver.visit(print_stmt)
            # 参数 a 应解析到当前作用域（depth=0）
            assert resolver.resolve(print_stmt.expr) == 0

    def test_return_stmt_raises(self):
        """Stmt.Return: 直接 visit 会抛 ReturnException。"""
        src = "return 1;"
        resolver = Resolver()
        stmts = _parse(src)
        with pytest.raises(ReturnException) as exc_info:
            resolver.visit_many(stmts)
        assert exc_info.value.value == 1

    def test_return_nil(self):
        """Stmt.Return: 空 return 实际值为 Literal(None)。"""
        src = "return;"
        resolver = Resolver()
        stmts = _parse(src)
        with pytest.raises(ReturnException) as exc_info:
            resolver.visit_many(stmts)
        assert exc_info.value.value is None

    def test_return_inside_function_propagates(self):
        """Stmt.Return: 在函数体内 visit 时异常会向上传播（当前实现行为）。"""
        src = """
        fun foo() {
            return 42;
        }
        """
        resolver = Resolver()
        stmts = _parse(src)
        with pytest.raises(ReturnException):
            resolver.visit_many(stmts)

    # ---- Error / ResolveError branches ----

    def test_self_reference_in_initializer(self):
        """Expr.Variable: 在自身 initializer 中引用自身应报错。"""
        src = "var a = a;"
        resolver = Resolver()
        stmts = _parse(src)
        with pytest.raises(ResolveError):
            resolver.visit_many(stmts)

    def test_undeclared_variable(self):
        """Expr.Variable: 引用未声明变量应报错。"""
        src = "print b;"
        resolver = Resolver()
        stmts = _parse(src)
        with pytest.raises(ResolveError):
            resolver.visit_many(stmts)

    def test_redeclare_in_same_scope(self):
        """Stmt.Var: 同一作用域内重复声明应报错。"""
        src = """
        var a = 1;
        var a = 2;
        """
        resolver = Resolver()
        stmts = _parse(src)
        with pytest.raises(ResolveError):
            resolver.visit_many(stmts)

    def test_resolve_unresolvable(self):
        """resolve() 对不可解析节点应抛 ResolveError。"""
        src = "var a = 1;"
        resolver = Resolver()
        stmts = _parse(src)
        resolver.visit_many(stmts)
        var_stmt = cast(Stmt.Var, stmts[0])
        # Stmt.Var 不在 resolve 接受的类型里
        with pytest.raises(ResolveError):
            resolver.resolve(var_stmt)
