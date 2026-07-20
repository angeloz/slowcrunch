import math

from slowcrunch.core.ast import (
    AssignNode,
    BinaryOpNode,
    CallNode,
    FunctionDefNode,
    NameNode,
    NumberNode,
    ProgramNode,
    UnaryOpNode,
)
from slowcrunch.core.errors import EvaluationError
from slowcrunch.runtime.user_functions import UserFunction


class Evaluator:
    def __init__(self, context, local_variables=None):
        self.context = context
        self.local_variables = local_variables or {}

    def evaluate(self, node):
        if isinstance(node, ProgramNode):
            result = None
            for statement in node.statements:
                result = self.evaluate(statement)
                if isinstance(result, (int, float)):
                    self.context.set_ans(result)
            return result

        if isinstance(node, AssignNode):
            value = self.evaluate(node.value)
            self.context.set_variable(node.name, value)
            return value

        if isinstance(node, FunctionDefNode):
            self.context.set_function(node.name, node.parameters, node.body)
            return f"Defined {node.name}({', '.join(node.parameters)})"

        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, NameNode):
            if node.name in self.local_variables:
                return self.local_variables[node.name]
            return self.context.get_variable(node.name)

        if isinstance(node, UnaryOpNode):
            operand = self.evaluate(node.operand)
            if node.operator == "+":
                return operand
            if node.operator == "-":
                return -operand
            raise EvaluationError(f"Unsupported unary operator: {node.operator}")

        if isinstance(node, BinaryOpNode):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            return self.apply_binary_operator(node.operator, left, right)

        if isinstance(node, CallNode):
            function = self.context.get_function(node.name)
            arguments = [self.evaluate(argument) for argument in node.arguments]
            return self.call_function(function, arguments)

        raise EvaluationError(f"Unsupported node: {type(node).__name__}")

    def call_function(self, function, arguments):
        if isinstance(function, UserFunction):
            expected = len(function.parameters)
            received = len(arguments)
            if received != expected:
                raise EvaluationError(
                    f"Function '{function.name}' expects {expected} argument(s), got {received}."
                )
            local_variables = dict(zip(function.parameters, arguments))
            return Evaluator(self.context, local_variables).evaluate(function.body)

        try:
            return function(*arguments)
        except TypeError as error:
            raise EvaluationError("Invalid arguments for function call.") from error
        except ValueError as error:
            raise EvaluationError(str(error)) from error

    def apply_binary_operator(self, operator, left, right):
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            if right == 0:
                raise EvaluationError("Division by zero is not allowed.")
            return left / right
        if operator == "^":
            return math.pow(left, right)
        raise EvaluationError(f"Unsupported operator: {operator}")
