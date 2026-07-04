from .base import Expression, LiteralTypes
from .token import Token


class Binary(Expression):
    def __init__(self, left: Expression, operator: Token, right: Expression):
        self.left = left
        self.operator = operator
        self.right = right

    # def accept(self, visitor: Expr.Visitor):
    #     return visitor.visit(self)


class Unary(Expression):
    def __init__(self, operator: Token, right: Expression):
        self.operator = operator
        self.right = right

    # def accept(self, visitor: Expr.Visitor):
    #     return visitor.visit(self)


class Literal(Expression):
    def __init__(self, value: LiteralTypes):
        self.value = value

    # def accept(self, visitor: Expr.Visitor):
    #     return visitor.visit(self)


class Grouping(Expression):
    def __init__(self, expr: Expression):
        self.expr = expr


class Variable(Expression):
    def __init__(self, identify: Token):
        self.identify = identify


class Assign(Expression):
    def __init__(self, identify: Token, value: Expression):
        self.identify = identify
        self.value = value


class Logical(Expression):
    def __init__(self, left: Expression, operator: Token, right: Expression):
        self.left = left
        self.operator = operator
        self.right = right

class Call(Expression):
    def __init__(self, expr: Expression, arguments: list[Expression]):
        self.expr = expr
        self.arguments = arguments

class Expr:
    Binary = Binary
    Unary = Unary
    Literal = Literal
    Grouping = Grouping
    Variable = Variable
    Assign = Assign
    Logical = Logical
    Call = Call
