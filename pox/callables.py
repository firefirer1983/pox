from .statement import Stmt
from .base import PoxCallable


class PoxFunction(PoxCallable):
    def __init__(self, stmt: Stmt.Function):
        self.stmt = stmt

    def arity(self):
        return len(self.stmt.parameters)

    def to_str(self) -> str:
        parameters = ",".join(self.stmt.parameters) or ""
        return f"fun<{self.stmt.name}({parameters})>"

    @property
    def block(self) -> Stmt.Block:
        return self.stmt.block

    @property
    def parameters(self) -> list[str]:
        return self.stmt.parameters
