from dataclasses import dataclass

from slowcrunch.core.ast import (
    AssignNode,
    BinaryOpNode,
    CallNode,
    FunctionDefNode,
    ListNode,
    NameNode,
    NumberNode,
    ProgramNode,
    UnaryOpNode,
)
from slowcrunch.core.errors import EvaluationError
from slowcrunch.runtime.builtins import ANGLE_RETURNING_FUNCTIONS
from slowcrunch.runtime.numbers import is_numeric, normalize_number
from slowcrunch.runtime.user_functions import UserFunction


@dataclass(frozen=True)
class EvaluatedValue:
    value: object
    kind: str | None = None


class Evaluator:
    def __init__(self, context, local_variables=None):
        self.context = context
        self.local_variables = local_variables or {}

    def evaluate(self, node):
        return self.evaluate_with_kind(node).value

    def evaluate_with_kind(self, node):
        if isinstance(node, ProgramNode):
            result = EvaluatedValue(None)
            for statement in node.statements:
                result = self.evaluate_with_kind(statement)
                if is_numeric(result.value):
                    self.context.set_ans(result.value, result.kind)
            return result

        if isinstance(node, AssignNode):
            value = self.evaluate_with_kind(node.value)
            self.context.set_variable(node.name, value.value, value.kind)
            return value

        if isinstance(node, FunctionDefNode):
            self.context.set_function(node.name, node.parameters, node.body)
            return EvaluatedValue(f"Defined {node.name}({', '.join(node.parameters)})")

        if isinstance(node, NumberNode):
            return EvaluatedValue(node.value, node.value_kind)

        if isinstance(node, ListNode):
            return EvaluatedValue([self.evaluate_with_kind(item).value for item in node.items])

        if isinstance(node, NameNode):
            if node.name in self.local_variables:
                return self.local_variables[node.name]
            return EvaluatedValue(
                self.context.get_variable(node.name),
                self.context.get_variable_kind(node.name),
            )

        if isinstance(node, UnaryOpNode):
            operand = self.evaluate_with_kind(node.operand)
            if isinstance(operand.value, list):
                raise EvaluationError("Unary operators do not support list values.")
            if node.operator == "+":
                return EvaluatedValue(normalize_number(operand.value), operand.kind)
            if node.operator == "-":
                return EvaluatedValue(normalize_number(-operand.value), operand.kind)
            raise EvaluationError(f"Unsupported unary operator: {node.operator}")

        if isinstance(node, BinaryOpNode):
            left = self.evaluate_with_kind(node.left)
            right = self.evaluate_with_kind(node.right)
            return self.apply_binary_operator(node.operator, left, right)

        if isinstance(node, CallNode):
            function = self.context.get_function(node.name)
            arguments = [self.evaluate_with_kind(argument) for argument in node.arguments]
            return self.call_function(node.name, function, arguments)

        raise EvaluationError(f"Unsupported node: {type(node).__name__}")

    def call_function(self, function_name, function, arguments):
        if isinstance(function, UserFunction):
            expected = len(function.parameters)
            received = len(arguments)
            if received != expected:
                raise EvaluationError(
                    f"Function '{function.name}' expects {expected} argument(s), got {received}."
                )
            local_variables = dict(zip(function.parameters, arguments))
            return Evaluator(self.context, local_variables).evaluate_with_kind(function.body)

        try:
            result = self._normalize(function(*[argument.value for argument in arguments]))
            return EvaluatedValue(result, self._infer_function_kind(function_name, arguments, result))
        except TypeError as error:
            raise EvaluationError("Invalid arguments for function call.") from error
        except ValueError as error:
            raise EvaluationError(str(error)) from error
        except ZeroDivisionError as error:
            raise EvaluationError("Division by zero is not allowed.") from error

    def apply_binary_operator(self, operator, left, right):
        if isinstance(left.value, list) or isinstance(right.value, list):
            raise EvaluationError("List values do not support arithmetic operators yet.")

        try:
            if operator == "+":
                result = self._normalize(left.value + right.value)
                return EvaluatedValue(result, left.kind if left.kind == right.kind else None)
            if operator == "-":
                result = self._normalize(left.value - right.value)
                return EvaluatedValue(result, left.kind if left.kind == right.kind else None)
            if operator == "*":
                result = self._normalize(left.value * right.value)
                return EvaluatedValue(result, self._scaled_result_kind(left.kind, right.kind))
            if operator == "/":
                if right.value == 0:
                    raise EvaluationError("Division by zero is not allowed.")
                result = self._normalize(left.value / right.value)
                return EvaluatedValue(result, left.kind if left.kind and right.kind is None else None)
            if operator == "^":
                return EvaluatedValue(self._normalize(left.value ** right.value))
        except TypeError as error:
            raise EvaluationError(f"Invalid operands for operator '{operator}'.") from error

        raise EvaluationError(f"Unsupported operator: {operator}")

    def _scaled_result_kind(self, left_kind, right_kind):
        if left_kind and right_kind:
            return None
        return left_kind or right_kind

    def _infer_function_kind(self, function_name, arguments, result):
        if not is_numeric(result):
            return None
        if function_name == "abs" and len(arguments) == 1:
            return arguments[0].kind
        if function_name in ANGLE_RETURNING_FUNCTIONS:
            return "angle"
        return None

    def _normalize(self, value):
        return normalize_number(value)
