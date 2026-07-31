"""Public API for parsing and evaluating expressions."""

from slowcrunch.core.evaluator import Evaluator
from slowcrunch.core.parser import Parser
from slowcrunch.core.tokenizer import tokenize
from slowcrunch.runtime.context import EvaluationContext


def parse_input(text):
    tokens = tokenize(text)
    return Parser(tokens).parse()


def evaluate_expression(text, context=None):
    context = context or EvaluationContext()
    ast = parse_input(text)
    if not ast.statements:
        return None, context
    evaluated = Evaluator(context).evaluate_with_kind(ast)
    result = evaluated.value
    context.record_entry(text, result, evaluated.kind)
    return result, context
