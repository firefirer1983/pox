import logging
from typing import Optional, Any

from .base import LiteralTypes, RunError

logger = logging.getLogger(__name__)


GLOBAL_LEVEL = 0


class Environment:
    def __init__(self, enclosing: Optional["Environment"] = None):
        self.enclosing = enclosing
        self.vars: dict[str, Any] = dict()

    def define(self, name: str, value: Any):
        logger.info(f"var {name} = {value}")
        self.vars[name] = value

    def get(self, name: str) -> Any:
        if name in self.vars:
            logger.info(f"EnvGet({self.level}): {name} = {self.vars[name]}")
            return self.vars[name]
        if self.enclosing:
            return self.enclosing.get(name)
        raise RunError(f"Variable get {name} not found!")

    def assign(self, name: str, value: Any):
        if name in self.vars:
            logger.info(f"EnvAssign({self.level}): {name} = {self.vars[name]}")
            self.vars[name] = value
            return
        if self.enclosing:
            return self.enclosing.assign(name, value)
        raise RunError(f"Variable assign {name} not found!")

    @property
    def level(self) -> int:
        i = GLOBAL_LEVEL
        enclosing = self.enclosing
        while enclosing:
            i += 1
            enclosing = enclosing.enclosing
        return i


global_env = Environment()
