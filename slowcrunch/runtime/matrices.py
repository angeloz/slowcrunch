from slowcrunch.runtime.numbers import is_numeric, normalize_number


def require_vector(value, function_name, argument_name="argument"):
    if not isinstance(value, list):
        raise ValueError(f"Function '{function_name}' expects {argument_name} to be a vector.")
    if any(not _is_number(item) for item in value):
        raise ValueError(
            f"Function '{function_name}' expects {argument_name} to be a vector of numbers."
        )
    return value


def require_matrix(value, function_name, argument_name="argument"):
    if not isinstance(value, list):
        raise ValueError(f"Function '{function_name}' expects {argument_name} to be a matrix.")
    if not value:
        raise ValueError(f"Function '{function_name}' does not accept an empty matrix.")
    if not all(isinstance(row, list) for row in value):
        raise ValueError(f"Function '{function_name}' expects {argument_name} to be a matrix of rows.")

    column_count = len(value[0])
    if column_count == 0:
        raise ValueError(f"Function '{function_name}' does not accept matrices with empty rows.")
    for index, row in enumerate(value, start=1):
        if len(row) != column_count:
            raise ValueError(
                f"Function '{function_name}' requires a rectangular matrix; "
                f"row {index} has {len(row)} item(s), expected {column_count}."
            )
        if any(not _is_number(item) for item in row):
            raise ValueError(f"Function '{function_name}' expects matrix entries to be numbers.")
    return value


def require_square_matrix(value, function_name, argument_name="argument"):
    matrix = require_matrix(value, function_name, argument_name)
    if len(matrix) != len(matrix[0]):
        raise ValueError(f"Function '{function_name}' requires a square matrix.")
    return matrix


def vector_or_matrix_shape(value, function_name):
    if not isinstance(value, list):
        raise ValueError(f"Function '{function_name}' expects a vector or matrix.")
    if any(isinstance(item, list) for item in value):
        matrix = require_matrix(value, function_name)
        return [len(matrix), len(matrix[0])]
    return [len(require_vector(value, function_name))]


def multiply_matrices(left, right):
    return [
        [
            normalize_number(sum(left[row][index] * right[index][column] for index in range(len(right))))
            for column in range(len(right[0]))
        ]
        for row in range(len(left))
    ]


def determinant(matrix):
    working = [list(row) for row in matrix]
    sign = 1
    result = 1
    for column in range(len(working)):
        pivot_row = _pivot_row(working, column)
        if working[pivot_row][column] == 0:
            return 0.0
        if pivot_row != column:
            working[column], working[pivot_row] = working[pivot_row], working[column]
            sign *= -1
        pivot = working[column][column]
        result *= pivot
        for row in range(column + 1, len(working)):
            factor = working[row][column] / pivot
            for index in range(column + 1, len(working)):
                working[row][index] -= factor * working[column][index]
    return normalize_number(sign * result)


def inverse_matrix(matrix, function_name):
    size = len(matrix)
    augmented = [
        list(row) + [1.0 if row_index == column else 0.0 for column in range(size)]
        for row_index, row in enumerate(matrix)
    ]
    _reduce_to_identity(augmented, size, function_name)
    return [
        [normalize_number(value) for value in row[size:]]
        for row in augmented
    ]


def solve_linear_system(matrix, vector, function_name):
    size = len(matrix)
    augmented = [list(row) + [vector[index]] for index, row in enumerate(matrix)]
    _reduce_to_identity(augmented, size, function_name)
    return [normalize_number(row[-1]) for row in augmented]


def _reduce_to_identity(augmented, size, function_name):
    for column in range(size):
        pivot_row = _pivot_row(augmented, column)
        if augmented[pivot_row][column] == 0:
            raise ValueError(f"Function '{function_name}' requires a non-singular matrix.")
        if pivot_row != column:
            augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]

        pivot = augmented[column][column]
        augmented[column] = [value / pivot for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column])
            ]


def _pivot_row(matrix, column):
    return max(range(column, len(matrix)), key=lambda row: abs(matrix[row][column]))


def _is_number(value):
    return not isinstance(value, bool) and is_numeric(value)
