import logging
from typing import Optional, Any
from pprint import pformat
from .base import LiteralTypes, RunError
from .token import Token

logger = logging.getLogger(__name__)


GLOBAL_LEVEL = 0


def sprintf_env(env: "Environment", spaces: int = 1)-> str:
    stack: list["Environment"] =[]
    data = dict()
    cur = env
    while cur:
        stack.append(cur)
        cur = cur.enclosing

    while stack:
        cur = stack.pop()
        data = {**data, **cur.vars}
    return pformat(data, indent=2)


class Environment:
    def __init__(self, enclosing: Optional["Environment"] = None):
        self.enclosing = enclosing
        self.vars: dict[str, Any] = dict()

    def __repr__(self)-> str:
        return sprintf_env(self)

    def __str__(self) -> str:
        return repr(self)

    def define(self, name: str, value: Any):
        logger.info(f"var {name} = {value}")
        self.vars[name] = value

    def get(self, name: Token) -> Any:
        if name.lexeme in self.vars:
            logger.info(f"EnvGet({self.level}): {name} = {self.vars[name.lexeme]}")
            return self.vars[name.lexeme]
        if self.enclosing:
            return self.enclosing.get(name)
        raise RunError(f"Variable get {name.lexeme} at line:{name.line} not found!")

    def get_at(self, name: Token, distance: int) -> Any:
        try:
            env = self.get_ancestor(distance)
        except KeyError:
            raise RunError(
                f"Cant get variable: {name.lexeme} at line: {name.line}, for no env at distance:{distance}"
            )
        if name.lexeme not in env.vars:
            raise RunError(f"Cant get variable: {name.lexeme} at line: {name.line}")
        return env.vars[name.lexeme]

    def get_ancestor(self, distance: int) -> "Environment":
        cur = self
        for i in range(distance):
            if cur.enclosing:
                cur = cur.enclosing
            else:
                raise KeyError(f"Environment at distance: {distance} not available ")
        return cur

    def assign_at(self, name: Token, value: Any, distance: int) -> Any:
        try:
            env = self.get_ancestor(distance)
        except KeyError:
            raise RunError(
                f"Cant get variable: {name.lexeme} at line: {name.line}, for no env at distance:{distance}"
            )
        if name.lexeme not in env.vars:
            raise RunError(
                f"Cant get variable: {name.lexeme} at line: {name.line} at env distance: {distance}"
            )
        env.vars[name.lexeme] = value

    def assign(self, name: Token, value: Any):
        if name.lexeme in self.vars:
            logger.info(
                f"EnvAssign({self.level}): {name.lexeme} = {self.vars[name.lexeme]}"
            )
            self.vars[name.lexeme] = value
            return
        if self.enclosing:
            return self.enclosing.assign(name, value)
        raise RunError(f"Variable assign {name.lexeme} in line:{name.line} not found!")

    @property
    def level(self) -> int:
        i = GLOBAL_LEVEL
        enclosing = self.enclosing
        while enclosing:
            i += 1
            enclosing = enclosing.enclosing
        return i


global_env = Environment()
