"""Public API for parsing and evaluating expressions."""

from numbers import Number

from slowcrunch.core.evaluator import Evaluator
from slowcrunch.core.parser import Parser
from slowcrunch.core.tokenizer import tokenize
from slowcrunch.runtime.context import EvaluationContext


def evaluate_expression(text, context=None):
    context = context or EvaluationContext()
    tokens = tokenize(text)
    ast = Parser(tokens).parse()
    result = Evaluator(context).evaluate(ast)
    if isinstance(result, Number):
        context.set_ans(result)
    context.record_entry(text, result)
    return result, context
