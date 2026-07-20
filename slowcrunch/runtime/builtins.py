import cmath
import math

from slowcrunch.runtime.numbers import normalize_number


def _wrap_math_function(function):
    def wrapped(*arguments):
        return normalize_number(function(*arguments))

    return wrapped


def _real_part(value):
    return value.real if isinstance(value, complex) else value


def _imaginary_part(value):
    return value.imag if isinstance(value, complex) else 0.0


def _conjugate(value):
    return value.conjugate() if isinstance(value, complex) else value


def _argument(value):
    return cmath.phase(value)


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
        "arg": _wrap_math_function(_argument),
        "conj": _wrap_math_function(_conjugate),
        "cos": _wrap_math_function(cmath.cos),
        "im": _wrap_math_function(_imaginary_part),
        "log": _wrap_math_function(cmath.log),
        "re": _wrap_math_function(_real_part),
        "sin": _wrap_math_function(cmath.sin),
        "sqrt": _wrap_math_function(cmath.sqrt),
        "tan": _wrap_math_function(cmath.tan),
    }
