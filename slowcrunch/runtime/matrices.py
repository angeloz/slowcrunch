from slowcrunch.runtime.numbers import is_numeric, normalize_number

REDUCTION_TOLERANCE = 1e-12


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


def identity_matrix(size):
    return [
        [1.0 if row == column else 0.0 for column in range(size)]
        for row in range(size)
    ]


def diagonal_matrix(vector):
    return [
        [value if row == column else 0.0 for column in range(len(vector))]
        for row, value in enumerate(vector)
    ]


def vector_norm(vector):
    return sum(abs(value) ** 2 for value in vector) ** 0.5


def cross_product(left, right):
    return [
        normalize_number(left[1] * right[2] - left[2] * right[1]),
        normalize_number(left[2] * right[0] - left[0] * right[2]),
        normalize_number(left[0] * right[1] - left[1] * right[0]),
    ]


def rotation_2d(angle):
    import math

    cosine = _normalize_reduction_value(math.cos(angle))
    sine = _normalize_reduction_value(math.sin(angle))
    return [[cosine, -sine], [sine, cosine]]


def scale_2d(x_scale, y_scale):
    return [[x_scale, 0.0], [0.0, y_scale]]


def shear_2d(xy_shear, yx_shear):
    return [[1.0, xy_shear], [yx_shear, 1.0]]


def reflection_2d(direction):
    length_squared = sum(value * value for value in direction)
    if length_squared == 0:
        raise ValueError("Function 'reflect2d' requires a non-zero direction vector.")
    x_value, y_value = direction
    return [
        [
            _normalize_reduction_value((2 * x_value * x_value / length_squared) - 1),
            _normalize_reduction_value(2 * x_value * y_value / length_squared),
        ],
        [
            _normalize_reduction_value(2 * x_value * y_value / length_squared),
            _normalize_reduction_value((2 * y_value * y_value / length_squared) - 1),
        ],
    ]


def apply_matrix(matrix, vector):
    return [
        normalize_number(sum(value * vector[index] for index, value in enumerate(row)))
        for row in matrix
    ]


def matrix_trace(matrix):
    return sum(matrix[index][index] for index in range(len(matrix)))


def reduced_row_echelon_form(matrix):
    working = [list(row) for row in matrix]
    pivot_row = 0
    for column in range(len(working[0])):
        if pivot_row == len(working):
            break
        candidate_row = _pivot_row(working, column, pivot_row)
        if abs(working[candidate_row][column]) <= REDUCTION_TOLERANCE:
            continue
        if candidate_row != pivot_row:
            working[pivot_row], working[candidate_row] = working[candidate_row], working[pivot_row]

        pivot = working[pivot_row][column]
        working[pivot_row] = [value / pivot for value in working[pivot_row]]
        for row in range(len(working)):
            if row == pivot_row:
                continue
            factor = working[row][column]
            working[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(working[row], working[pivot_row])
            ]
        pivot_row += 1
    return [[_normalize_reduction_value(value) for value in row] for row in working]


def matrix_rank(matrix):
    reduced = reduced_row_echelon_form(matrix)
    return sum(any(abs(value) > REDUCTION_TOLERANCE for value in row) for row in reduced)


def least_squares_solution(matrix, vector, function_name):
    row_count = len(matrix)
    column_count = len(matrix[0])
    if row_count < column_count:
        raise ValueError(
            f"Function '{function_name}' requires at least as many rows as columns."
        )

    q_columns = []
    upper = [[0.0 for _ in range(column_count)] for _ in range(column_count)]
    for column in range(column_count):
        values = [matrix[row][column] for row in range(row_count)]
        for previous, q_column in enumerate(q_columns):
            coefficient = sum(
                q_value.conjugate() * value
                for q_value, value in zip(q_column, values)
            )
            upper[previous][column] = coefficient
            values = [
                value - coefficient * q_value
                for value, q_value in zip(values, q_column)
            ]

        length = vector_norm(values)
        if length <= REDUCTION_TOLERANCE:
            raise ValueError(f"Function '{function_name}' requires linearly independent columns.")
        upper[column][column] = length
        q_columns.append([value / length for value in values])

    projected = [
        sum(q_value.conjugate() * value for q_value, value in zip(q_column, vector))
        for q_column in q_columns
    ]
    solution = [0.0 for _ in range(column_count)]
    for row in range(column_count - 1, -1, -1):
        solution[row] = (
            projected[row] - sum(upper[row][column] * solution[column] for column in range(row + 1, column_count))
        ) / upper[row][row]
    return [normalize_number(value) for value in solution]


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


def _pivot_row(matrix, column, start_row=None):
    start = column if start_row is None else start_row
    return max(range(start, len(matrix)), key=lambda row: abs(matrix[row][column]))


def _normalize_reduction_value(value):
    if abs(value) <= REDUCTION_TOLERANCE:
        return 0.0
    return normalize_number(value)


def _is_number(value):
    return not isinstance(value, bool) and is_numeric(value)
