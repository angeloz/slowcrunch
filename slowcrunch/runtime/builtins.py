import cmath
import math

from slowcrunch.runtime.numbers import format_angle_dms, format_duration_hms, to_degrees

ANGLE_RETURNING_FUNCTIONS = {
    "acos",
    "acot",
    "acsc",
    "arg",
    "asec",
    "asin",
    "atan",
    "atan2",
}

BUILTIN_FUNCTION_GROUPS = (
    ("Trigonometric", ("sin", "cos", "tan", "cot", "sec", "csc")),
    ("Inverse trigonometric", ("asin", "acos", "atan", "atan2", "acot", "asec", "acsc", "arg")),
    ("Hyperbolic", ("sinh", "cosh", "tanh", "coth", "sech", "csch")),
    ("Inverse hyperbolic", ("asinh", "acosh", "atanh")),
    ("Exponential and logarithmic", ("exp", "ln", "log", "log10", "log2", "sqrt")),
    ("Complex and utility", ("abs", "floor", "ceil", "re", "im", "conj")),
    ("Statistics", ("len", "sum", "min", "max", "mean")),
    ("Formatting helpers", ("deg", "dms", "hms")),
)


def _wrap_math_function(function):
    def wrapped(*arguments):
        return function(*arguments)

    return wrapped


def _real_part(value):
    return value.real if isinstance(value, complex) else value


def _imaginary_part(value):
    return value.imag if isinstance(value, complex) else 0.0


def _conjugate(value):
    return value.conjugate() if isinstance(value, complex) else value


def _argument(value):
    return cmath.phase(value)


def _degrees(value):
    return to_degrees(value)


def _sec(value):
    return 1 / cmath.cos(value)


def _csc(value):
    return 1 / cmath.sin(value)


def _cot(value):
    return 1 / cmath.tan(value)


def _asec(value):
    return cmath.acos(1 / value)


def _acsc(value):
    return cmath.asin(1 / value)


def _acot(value):
    return (math.pi / 2) - cmath.atan(value)


def _atan2(y_value, x_value):
    return math.atan2(y_value, x_value)


def _sech(value):
    return 1 / cmath.cosh(value)


def _csch(value):
    return 1 / cmath.sinh(value)


def _coth(value):
    return 1 / cmath.tanh(value)


def _log2(value):
    return cmath.log(value, 2)


def _require_list(value, function_name):
    if not isinstance(value, list):
        raise ValueError(f"Function '{function_name}' expects a list argument.")
    return value


def _require_real_number_list(value, function_name, allow_empty=False):
    items = _require_list(value, function_name)
    if not items and not allow_empty:
        raise ValueError(f"Function '{function_name}' does not accept an empty list.")

    normalized_items = []
    for item in items:
        if isinstance(item, bool) or isinstance(item, complex) or not isinstance(item, (int, float)):
            raise ValueError(f"Function '{function_name}' expects a list of real numbers.")
        normalized_items.append(float(item))
    return normalized_items


def _list_length(value):
    return len(_require_list(value, "len"))


def _list_sum(value):
    return math.fsum(_require_real_number_list(value, "sum", allow_empty=True))


def _list_min(value):
    return min(_require_real_number_list(value, "min"))


def _list_max(value):
    return max(_require_real_number_list(value, "max"))


def _list_mean(value):
    items = _require_real_number_list(value, "mean")
    return math.fsum(items) / len(items)


def builtin_function_groups():
    return BUILTIN_FUNCTION_GROUPS


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
        "acos": _wrap_math_function(cmath.acos),
        "acosh": _wrap_math_function(cmath.acosh),
        "acot": _wrap_math_function(_acot),
        "acsc": _wrap_math_function(_acsc),
        "arg": _wrap_math_function(_argument),
        "asec": _wrap_math_function(_asec),
        "asin": _wrap_math_function(cmath.asin),
        "asinh": _wrap_math_function(cmath.asinh),
        "atan": _wrap_math_function(cmath.atan),
        "atan2": _wrap_math_function(_atan2),
        "atanh": _wrap_math_function(cmath.atanh),
        "ceil": _wrap_math_function(math.ceil),
        "conj": _wrap_math_function(_conjugate),
        "cos": _wrap_math_function(cmath.cos),
        "cosh": _wrap_math_function(cmath.cosh),
        "cot": _wrap_math_function(_cot),
        "coth": _wrap_math_function(_coth),
        "csc": _wrap_math_function(_csc),
        "csch": _wrap_math_function(_csch),
        "deg": _wrap_math_function(_degrees),
        "dms": _wrap_math_function(format_angle_dms),
        "exp": _wrap_math_function(cmath.exp),
        "floor": _wrap_math_function(math.floor),
        "hms": _wrap_math_function(format_duration_hms),
        "im": _wrap_math_function(_imaginary_part),
        "ln": _wrap_math_function(cmath.log),
        "log": _wrap_math_function(cmath.log),
        "log10": _wrap_math_function(cmath.log10),
        "log2": _wrap_math_function(_log2),
        "len": _wrap_math_function(_list_length),
        "max": _wrap_math_function(_list_max),
        "mean": _wrap_math_function(_list_mean),
        "min": _wrap_math_function(_list_min),
        "re": _wrap_math_function(_real_part),
        "sec": _wrap_math_function(_sec),
        "sin": _wrap_math_function(cmath.sin),
        "sinh": _wrap_math_function(cmath.sinh),
        "sum": _wrap_math_function(_list_sum),
        "sqrt": _wrap_math_function(cmath.sqrt),
        "tan": _wrap_math_function(cmath.tan),
        "tanh": _wrap_math_function(cmath.tanh),
    }
