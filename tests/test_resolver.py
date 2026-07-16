import time
from typing import cast
from pox.callables import PoxFunction
from pox.environment import global_env
from pox.interpreter import Interpreter
from pox.resolver import Resolver
from pox.parser import Parser
from pox.scanner import Scanner
from pox.statement import Stmt

class TestResolverStmt:
    def test_var_expr(self):
        src = """
        var a = 5;
        """
        resolver = Resolver()
        stmts = Parser(Scanner(src).scan_tokens()).parse()
        assert len(stmts) == 1
        resolver.visit_many(stmts)
        resolver.resolve(stmts[0])
