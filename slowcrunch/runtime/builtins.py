import cmath
import math

from slowcrunch.runtime.numbers import normalize_number


def _wrap_math_function(function):
    def wrapped(*arguments):
        return normalize_number(function(*arguments))

    return wrapped


def build_builtin_variables():
    return {
        "ans": 0.0,
        "e": math.e,
        "i": 1j,
        "pi": math.pi,
    }


def build_builtin_functions():
    return {
        "abs": abs,
        "cos": _wrap_math_function(cmath.cos),
        "log": _wrap_math_function(cmath.log),
        "sin": _wrap_math_function(cmath.sin),
        "sqrt": _wrap_math_function(cmath.sqrt),
        "tan": _wrap_math_function(cmath.tan),
    }
