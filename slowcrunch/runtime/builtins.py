import math


def build_builtin_variables():
    return {
        "ans": 0.0,
        "e": math.e,
        "pi": math.pi,
    }


def build_builtin_functions():
    return {
        "abs": abs,
        "cos": math.cos,
        "log": math.log,
        "sin": math.sin,
        "sqrt": math.sqrt,
        "tan": math.tan,
    }
