from .token import Token
from .base import RunError
from typing import Any
from typing import Optional


class Environment:
    def __init__(self, enclosing: Optional[Environment] = None):
        self.enclosing = enclosing
        self.vars: dict[str, Any] = dict()

    def define(self, name: str, value: Any):
        self.vars[name] = value

    def get(self, name: Token):
        env = self
        while env:
            result = env.vars.get(name.lexeme)
            if result:
                return result
            env = self.enclosing
        raise RunError(f"Variable get {name.lexeme} not found!")

    def assign(self, name: Token, value: Any):
        env = self
        while env:
            if name.lexeme in env.vars.keys():
                env.vars[name.lexeme] = value
                return
            env = self.enclosing
        raise RunError(f"Variable assign {name.lexeme} not found!")
