import math

from slowcrunch.core.ast import AssignNode, BinaryOpNode, CallNode, NameNode, NumberNode, UnaryOpNode
from slowcrunch.core.errors import EvaluationError


class Evaluator:
    def __init__(self, context):
        self.context = context

    def evaluate(self, node):
        if isinstance(node, AssignNode):
            value = self.evaluate(node.value)
            self.context.set_variable(node.name, value)
            return value

        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, NameNode):
            return self.context.get_variable(node.name)

        if isinstance(node, UnaryOpNode):
            operand = self.evaluate(node.operand)
            if node.operator == "+":
                return operand
            if node.operator == "-":
                return -operand
            raise EvaluationError(f"Operatore unario non supportato: {node.operator}")

        if isinstance(node, BinaryOpNode):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            return self.apply_binary_operator(node.operator, left, right)

        if isinstance(node, CallNode):
            function = self.context.get_function(node.name)
            arguments = [self.evaluate(argument) for argument in node.arguments]
            try:
                return function(*arguments)
            except TypeError as error:
                raise EvaluationError(f"Argomenti non validi per la funzione '{node.name}'.") from error
            except ValueError as error:
                raise EvaluationError(str(error)) from error

        raise EvaluationError(f"Nodo non supportato: {type(node).__name__}")

    def apply_binary_operator(self, operator, left, right):
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            if right == 0:
                raise EvaluationError("Non e' possibile dividere per zero.")
            return left / right
        if operator == "^":
            return math.pow(left, right)
        raise EvaluationError(f"Operatore non supportato: {operator}")
