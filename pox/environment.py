from .base import LiteralTypes
from .base import RunError
from typing import Any
from typing import Optional


class Environment:
    def __init__(self, enclosing: Optional["Environment"] = None):
        self.enclosing = enclosing
        self.vars: dict[str, Any] = dict()

    def define(self, name: str, value: LiteralTypes):
        self.vars[name] = value

    def get(self, name: str) -> LiteralTypes:
        env = self
        while env:
            if name in env.vars:
                return env.vars[name]
            env = env.enclosing
        raise RunError(f"Variable get {name} not found!")

    def assign(self, name: str, value: LiteralTypes):
        env = self
        while env:
            if name in env.vars.keys():
                env.vars[name] = value
                return
            env = env.enclosing
        raise RunError(f"Variable assign {name} not found!")




global_env = Environment()
