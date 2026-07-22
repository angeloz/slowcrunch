import cmath
import math

from slowcrunch.runtime.numbers import format_angle_dms, format_duration_hms, to_degrees
from slowcrunch.runtime.matrices import (
    determinant,
    inverse_matrix,
    multiply_matrices,
    require_matrix,
    require_square_matrix,
    require_vector,
    solve_linear_system,
    vector_or_matrix_shape,
)

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
    (
        "Statistics",
        (
            "len",
            "sum",
            "min",
            "max",
            "mean",
            "median",
            "mode",
            "variance",
            "stdev",
            "sample_variance",
            "sample_stdev",
            "cov",
            "sample_cov",
            "corr",
            "linreg",
        ),
    ),
    ("Combinatorics", ("fact", "perm", "comb")),
    (
        "Linear algebra",
        ("shape", "rows", "cols", "transpose", "dot", "matmul", "det", "inv", "solve"),
    ),
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
    items = _require_number_list(value, function_name, allow_empty)
    if any(isinstance(item, complex) for item in items):
        raise ValueError(f"Function '{function_name}' expects a list of real numbers.")
    return [float(item) for item in items]


def _require_number_list(value, function_name, allow_empty=False):
    items = _require_list(value, function_name)
    if not items and not allow_empty:
        raise ValueError(f"Function '{function_name}' does not accept an empty list.")

    normalized_items = []
    for item in items:
        if isinstance(item, bool) or not isinstance(item, (int, float, complex)):
            raise ValueError(f"Function '{function_name}' expects a list of numbers.")
        normalized_items.append(item)
    return normalized_items


def _require_minimum_length(items, function_name, size):
    if len(items) < size:
        raise ValueError(f"Function '{function_name}' expects at least {size} value(s).")
    return items


def _require_paired_real_number_lists(x_values, y_values, function_name, minimum_length=1):
    x_items = _require_minimum_length(
        _require_real_number_list(x_values, function_name),
        function_name,
        minimum_length,
    )
    y_items = _require_minimum_length(
        _require_real_number_list(y_values, function_name),
        function_name,
        minimum_length,
    )
    if len(x_items) != len(y_items):
        raise ValueError(f"Function '{function_name}' expects lists of the same length.")
    return x_items, y_items


def _require_paired_number_lists(x_values, y_values, function_name, minimum_length=1):
    x_items = _require_minimum_length(
        _require_number_list(x_values, function_name),
        function_name,
        minimum_length,
    )
    y_items = _require_minimum_length(
        _require_number_list(y_values, function_name),
        function_name,
        minimum_length,
    )
    if len(x_items) != len(y_items):
        raise ValueError(f"Function '{function_name}' expects lists of the same length.")
    return x_items, y_items


def _require_non_negative_integer(value, function_name, argument_name=None):
    suffix = f" for {argument_name}" if argument_name else ""
    if isinstance(value, bool) or isinstance(value, complex) or not isinstance(value, (int, float)):
        raise ValueError(f"Function '{function_name}' expects a non-negative integer{suffix}.")
    normalized = float(value)
    if normalized < 0 or not normalized.is_integer():
        raise ValueError(f"Function '{function_name}' expects a non-negative integer{suffix}.")
    return int(normalized)


def _list_length(value):
    return len(_require_list(value, "len"))


def _list_sum(value):
    return sum(_require_number_list(value, "sum", allow_empty=True))


def _list_min(value):
    return min(_require_real_number_list(value, "min"))


def _list_max(value):
    return max(_require_real_number_list(value, "max"))


def _list_mean(value):
    items = _require_number_list(value, "mean")
    return sum(items) / len(items)


def _list_median(value):
    items = sorted(_require_real_number_list(value, "median"))
    midpoint = len(items) // 2
    if len(items) % 2 == 1:
        return items[midpoint]
    return (items[midpoint - 1] + items[midpoint]) / 2.0


def _list_mode(value):
    items = _require_real_number_list(value, "mode")
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1

    highest_count = max(counts.values())
    modes = [item for item, count in counts.items() if count == highest_count]
    if len(modes) != 1 or highest_count == 1:
        raise ValueError("Function 'mode' requires a unique mode.")
    return modes[0]


def _variance_from_items(items):
    mean_value = sum(items) / len(items)
    return sum(abs(item - mean_value) ** 2 for item in items) / len(items)


def _sample_variance_from_items(items):
    mean_value = sum(items) / len(items)
    return sum(abs(item - mean_value) ** 2 for item in items) / (len(items) - 1)


def _covariance_from_items(x_items, y_items):
    x_mean = sum(x_items) / len(x_items)
    y_mean = sum(y_items) / len(y_items)
    return sum(
        (x_value - x_mean) * (y_value - y_mean).conjugate()
        for x_value, y_value in zip(x_items, y_items)
    ) / len(x_items)


def _sample_covariance_from_items(x_items, y_items):
    x_mean = sum(x_items) / len(x_items)
    y_mean = sum(y_items) / len(y_items)
    return sum(
        (x_value - x_mean) * (y_value - y_mean).conjugate()
        for x_value, y_value in zip(x_items, y_items)
    ) / (len(x_items) - 1)


def _list_variance(value):
    items = _require_number_list(value, "variance")
    return _variance_from_items(items)


def _list_stdev(value):
    items = _require_number_list(value, "stdev")
    return math.sqrt(_variance_from_items(items))


def _list_sample_variance(value):
    items = _require_minimum_length(
        _require_number_list(value, "sample_variance"),
        "sample_variance",
        2,
    )
    return _sample_variance_from_items(items)


def _list_sample_stdev(value):
    items = _require_minimum_length(
        _require_number_list(value, "sample_stdev"),
        "sample_stdev",
        2,
    )
    return math.sqrt(_sample_variance_from_items(items))


def _list_covariance(x_values, y_values):
    x_items, y_items = _require_paired_number_lists(x_values, y_values, "cov")
    return _covariance_from_items(x_items, y_items)


def _list_sample_covariance(x_values, y_values):
    x_items, y_items = _require_paired_number_lists(
        x_values,
        y_values,
        "sample_cov",
        minimum_length=2,
    )
    return _sample_covariance_from_items(x_items, y_items)


def _list_correlation(x_values, y_values):
    x_items, y_items = _require_paired_number_lists(
        x_values,
        y_values,
        "corr",
        minimum_length=2,
    )
    x_stdev = math.sqrt(_variance_from_items(x_items))
    y_stdev = math.sqrt(_variance_from_items(y_items))
    if x_stdev == 0.0 or y_stdev == 0.0:
        raise ValueError("Function 'corr' requires non-constant input lists.")
    return _covariance_from_items(x_items, y_items) / (x_stdev * y_stdev)


def _list_linear_regression(x_values, y_values):
    x_items, y_items = _require_paired_real_number_lists(
        x_values,
        y_values,
        "linreg",
        minimum_length=2,
    )
    x_variance = _variance_from_items(x_items)
    if x_variance == 0.0:
        raise ValueError("Function 'linreg' requires a non-constant x list.")
    slope = _covariance_from_items(x_items, y_items) / x_variance
    intercept = (math.fsum(y_items) / len(y_items)) - slope * (math.fsum(x_items) / len(x_items))
    return [slope, intercept]


def _factorial(value):
    return math.factorial(_require_non_negative_integer(value, "fact"))


def _permutations(n_value, k_value):
    n_integer = _require_non_negative_integer(n_value, "perm", "n")
    k_integer = _require_non_negative_integer(k_value, "perm", "k")
    if k_integer > n_integer:
        raise ValueError("Function 'perm' requires k <= n.")
    return math.perm(n_integer, k_integer)


def _combinations(n_value, k_value):
    n_integer = _require_non_negative_integer(n_value, "comb", "n")
    k_integer = _require_non_negative_integer(k_value, "comb", "k")
    if k_integer > n_integer:
        raise ValueError("Function 'comb' requires k <= n.")
    return math.comb(n_integer, k_integer)


def _shape(value):
    return vector_or_matrix_shape(value, "shape")


def _matrix_rows(value):
    return len(require_matrix(value, "rows"))


def _matrix_columns(value):
    matrix = require_matrix(value, "cols")
    return len(matrix[0])


def _transpose(value):
    matrix = require_matrix(value, "transpose")
    return [[matrix[row][column] for row in range(len(matrix))] for column in range(len(matrix[0]))]


def _dot(left, right):
    left_vector = require_vector(left, "dot", "first argument")
    right_vector = require_vector(right, "dot", "second argument")
    if len(left_vector) != len(right_vector):
        raise ValueError("Function 'dot' expects vectors of the same length.")
    return sum(left_item * right_item for left_item, right_item in zip(left_vector, right_vector))


def _matrix_multiply(left, right):
    left_matrix = require_matrix(left, "matmul", "first argument")
    right_matrix = require_matrix(right, "matmul", "second argument")
    if len(left_matrix[0]) != len(right_matrix):
        raise ValueError(
            "Function 'matmul' requires the column count of the first matrix to "
            "match the row count of the second matrix."
        )
    return multiply_matrices(left_matrix, right_matrix)


def _determinant(value):
    return determinant(require_square_matrix(value, "det"))


def _inverse(value):
    return inverse_matrix(require_square_matrix(value, "inv"), "inv")


def _solve(matrix, vector):
    coefficient_matrix = require_square_matrix(matrix, "solve", "first argument")
    right_vector = require_vector(vector, "solve", "second argument")
    if len(right_vector) != len(coefficient_matrix):
        raise ValueError(
            "Function 'solve' requires the second argument to have one value for each matrix row."
        )
    return solve_linear_system(coefficient_matrix, right_vector, "solve")


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
        "comb": _wrap_math_function(_combinations),
        "conj": _wrap_math_function(_conjugate),
        "corr": _wrap_math_function(_list_correlation),
        "cos": _wrap_math_function(cmath.cos),
        "cosh": _wrap_math_function(cmath.cosh),
        "cot": _wrap_math_function(_cot),
        "coth": _wrap_math_function(_coth),
        "cov": _wrap_math_function(_list_covariance),
        "csc": _wrap_math_function(_csc),
        "csch": _wrap_math_function(_csch),
        "cols": _wrap_math_function(_matrix_columns),
        "deg": _wrap_math_function(_degrees),
        "det": _wrap_math_function(_determinant),
        "dms": _wrap_math_function(format_angle_dms),
        "dot": _wrap_math_function(_dot),
        "exp": _wrap_math_function(cmath.exp),
        "fact": _wrap_math_function(_factorial),
        "floor": _wrap_math_function(math.floor),
        "hms": _wrap_math_function(format_duration_hms),
        "im": _wrap_math_function(_imaginary_part),
        "inv": _wrap_math_function(_inverse),
        "ln": _wrap_math_function(cmath.log),
        "log": _wrap_math_function(cmath.log),
        "log10": _wrap_math_function(cmath.log10),
        "log2": _wrap_math_function(_log2),
        "len": _wrap_math_function(_list_length),
        "linreg": _wrap_math_function(_list_linear_regression),
        "max": _wrap_math_function(_list_max),
        "matmul": _wrap_math_function(_matrix_multiply),
        "mean": _wrap_math_function(_list_mean),
        "median": _wrap_math_function(_list_median),
        "min": _wrap_math_function(_list_min),
        "mode": _wrap_math_function(_list_mode),
        "perm": _wrap_math_function(_permutations),
        "re": _wrap_math_function(_real_part),
        "rows": _wrap_math_function(_matrix_rows),
        "sample_cov": _wrap_math_function(_list_sample_covariance),
        "sample_stdev": _wrap_math_function(_list_sample_stdev),
        "sample_variance": _wrap_math_function(_list_sample_variance),
        "sec": _wrap_math_function(_sec),
        "sin": _wrap_math_function(cmath.sin),
        "sinh": _wrap_math_function(cmath.sinh),
        "stdev": _wrap_math_function(_list_stdev),
        "sum": _wrap_math_function(_list_sum),
        "sqrt": _wrap_math_function(cmath.sqrt),
        "solve": _wrap_math_function(_solve),
        "shape": _wrap_math_function(_shape),
        "tan": _wrap_math_function(cmath.tan),
        "tanh": _wrap_math_function(cmath.tanh),
        "transpose": _wrap_math_function(_transpose),
        "variance": _wrap_math_function(_list_variance),
    }
