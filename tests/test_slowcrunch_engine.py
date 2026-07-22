import unittest
import math

from slowcrunch.core.errors import EvaluationError, IncompleteInputError, ParseError
from slowcrunch.engine import evaluate_expression, parse_input
from slowcrunch.runtime.context import EvaluationContext


class SlowCrunchEngineTest(unittest.TestCase):
    def test_operator_precedence(self):
        result, _ = evaluate_expression("1 + 2 * 3")
        self.assertEqual(result, 7.0)

    def test_parentheses(self):
        result, _ = evaluate_expression("(1 + 2) * 3")
        self.assertEqual(result, 9.0)

    def test_unary_operator(self):
        result, _ = evaluate_expression("-3 + 5")
        self.assertEqual(result, 2.0)

    def test_power_is_right_associative(self):
        result, _ = evaluate_expression("2 ^ 3 ^ 2")
        self.assertEqual(result, 512.0)

    def test_builtin_functions(self):
        result, _ = evaluate_expression("sqrt(9) + sin(0)")
        self.assertEqual(result, 3.0)

    def test_scientific_notation_literal(self):
        result, _ = evaluate_expression("1.2e6 + 3")
        self.assertEqual(result, 1200003.0)

    def test_list_literal(self):
        result, _ = evaluate_expression("[1, 2, 4, 5]")
        self.assertEqual(result, [1.0, 2.0, 4.0, 5.0])

    def test_empty_list_literal(self):
        result, _ = evaluate_expression("[]")
        self.assertEqual(result, [])

    def test_list_assignment_and_reuse(self):
        context = EvaluationContext()
        result, context = evaluate_expression("values = [1, 2 + 3, sqrt(16)]", context)
        self.assertEqual(result, [1.0, 5.0, 4.0])
        self.assertEqual(context.get_variable("values"), [1.0, 5.0, 4.0])

    def test_list_statistics_functions(self):
        result, _ = evaluate_expression("len([1, 2, 4, 5]) + sum([1, 2, 4, 5]) + min([1, 2, 4, 5]) + max([1, 2, 4, 5])")
        self.assertEqual(result, 22.0)
        result, _ = evaluate_expression("mean([1, 2, 4, 5])")
        self.assertEqual(result, 3.0)
        result, _ = evaluate_expression("median([1, 2, 4, 5])")
        self.assertEqual(result, 3.0)
        result, _ = evaluate_expression("mode([1, 1, 2])")
        self.assertEqual(result, 1.0)
        result, _ = evaluate_expression("variance([1, 2, 3])")
        self.assertAlmostEqual(result, 2.0 / 3.0)
        result, _ = evaluate_expression("stdev([1, 2, 3])")
        self.assertAlmostEqual(result, math.sqrt(2.0 / 3.0))
        result, _ = evaluate_expression("sample_variance([1, 2, 3])")
        self.assertEqual(result, 1.0)
        result, _ = evaluate_expression("sample_stdev([1, 2, 3])")
        self.assertEqual(result, 1.0)
        result, _ = evaluate_expression("cov([1, 2, 3], [2, 4, 6])")
        self.assertEqual(result, 4.0 / 3.0)
        result, _ = evaluate_expression("sample_cov([1, 2, 3], [2, 4, 6])")
        self.assertEqual(result, 2.0)
        result, _ = evaluate_expression("corr([1, 2, 3], [2, 4, 6])")
        self.assertEqual(result, 1.0)
        result, _ = evaluate_expression("linreg([1, 2, 3], [2, 4, 6])")
        self.assertEqual(result, [2.0, 0.0])

    def test_combinatorics_functions(self):
        result, _ = evaluate_expression("fact(5) + perm(5, 2) + comb(5, 2)")
        self.assertEqual(result, 150.0)

    def test_list_sum_accepts_empty_list(self):
        result, _ = evaluate_expression("sum([])")
        self.assertEqual(result, 0.0)

    def test_list_statistics_reject_non_list_arguments(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("mean(3)")
        self.assertEqual(str(error.exception), "Function 'mean' expects a list argument.")

    def test_list_statistics_reject_empty_list_when_required(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("mean([])")
        self.assertEqual(str(error.exception), "Function 'mean' does not accept an empty list.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("median([])")
        self.assertEqual(str(error.exception), "Function 'median' does not accept an empty list.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("mode([])")
        self.assertEqual(str(error.exception), "Function 'mode' does not accept an empty list.")

    def test_list_statistics_support_complex_numbers(self):
        result, _ = evaluate_expression("sum([1 + i, 2 - i])")
        self.assertEqual(result, 3.0)
        result, _ = evaluate_expression("mean([1 + i, 3 - i])")
        self.assertEqual(result, 2.0)
        result, _ = evaluate_expression("variance([1 + i, 1 - i])")
        self.assertEqual(result, 1.0)
        result, _ = evaluate_expression("stdev([1 + i, 1 - i])")
        self.assertEqual(result, 1.0)
        result, _ = evaluate_expression("cov([1 + i, 1 - i], [1 + i, 1 - i])")
        self.assertEqual(result, 1.0)
        result, _ = evaluate_expression("corr([1 + i, 1 - i], [1 + i, 1 - i])")
        self.assertEqual(result, 1.0)

    def test_ordered_list_statistics_reject_complex_numbers(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("median([1, 2i])")
        self.assertEqual(str(error.exception), "Function 'median' expects a list of real numbers.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("linreg([1, 2i], [3, 4])")
        self.assertEqual(str(error.exception), "Function 'linreg' expects a list of real numbers.")

    def test_sample_statistics_require_at_least_two_values(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("sample_variance([1])")
        self.assertEqual(str(error.exception), "Function 'sample_variance' expects at least 2 value(s).")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("sample_stdev([1])")
        self.assertEqual(str(error.exception), "Function 'sample_stdev' expects at least 2 value(s).")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("sample_cov([1], [2])")
        self.assertEqual(str(error.exception), "Function 'sample_cov' expects at least 2 value(s).")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("corr([1], [2])")
        self.assertEqual(str(error.exception), "Function 'corr' expects at least 2 value(s).")

    def test_mode_requires_unique_mode(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("mode([1, 2, 3])")
        self.assertEqual(str(error.exception), "Function 'mode' requires a unique mode.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("mode([1, 1, 2, 2])")
        self.assertEqual(str(error.exception), "Function 'mode' requires a unique mode.")

    def test_bivariate_statistics_require_matching_lengths(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("cov([1, 2], [3])")
        self.assertEqual(str(error.exception), "Function 'cov' expects lists of the same length.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("linreg([1, 2], [3, 4, 5])")
        self.assertEqual(str(error.exception), "Function 'linreg' expects lists of the same length.")

    def test_correlation_rejects_constant_inputs(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("corr([1, 1, 1], [2, 3, 4])")
        self.assertEqual(str(error.exception), "Function 'corr' requires non-constant input lists.")

    def test_linreg_rejects_constant_x_inputs(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("linreg([1, 1, 1], [2, 3, 4])")
        self.assertEqual(str(error.exception), "Function 'linreg' requires a non-constant x list.")

    def test_combinatorics_require_non_negative_integers(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("fact(2.5)")
        self.assertEqual(str(error.exception), "Function 'fact' expects a non-negative integer.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("perm(5, -1)")
        self.assertEqual(str(error.exception), "Function 'perm' expects a non-negative integer for k.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("comb(5, 6)")
        self.assertEqual(str(error.exception), "Function 'comb' requires k <= n.")

    def test_list_values_do_not_support_arithmetic_operators(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("[1, 2] + [3, 4]")
        self.assertEqual(str(error.exception), "List values do not support arithmetic operators yet.")

    def test_matrix_shape_and_dimensions(self):
        result, _ = evaluate_expression("shape([1, 2, 3])")
        self.assertEqual(result, [3.0])
        result, _ = evaluate_expression("shape([[1, 2], [3, 4]])")
        self.assertEqual(result, [2.0, 2.0])
        result, _ = evaluate_expression("rows([[1, 2], [3, 4]]) + cols([[1, 2], [3, 4]])")
        self.assertEqual(result, 4.0)

    def test_matrix_transpose_dot_and_multiply(self):
        result, _ = evaluate_expression("transpose([[1, 2, 3], [4, 5, 6]])")
        self.assertEqual(result, [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]])
        result, _ = evaluate_expression("dot([1, 2, 3], [4, 5, 6])")
        self.assertEqual(result, 32.0)
        result, _ = evaluate_expression("matmul([[1, 2], [3, 4]], [[5, 6], [7, 8]])")
        self.assertEqual(result, [[19.0, 22.0], [43.0, 50.0]])

    def test_matrix_functions_accept_complex_entries(self):
        result, _ = evaluate_expression("dot([1 + i, 2], [3, 4])")
        self.assertEqual(result, complex(11.0, 3.0))
        result, _ = evaluate_expression("matmul([[i]], [[i]])")
        self.assertEqual(result, [[-1.0]])

    def test_determinant_inverse_and_linear_system_solution(self):
        result, _ = evaluate_expression("det([[4, 7], [2, 6]])")
        self.assertEqual(result, 10.0)
        result, _ = evaluate_expression("inv([[4, 7], [2, 6]])")
        self.assertAlmostEqual(result[0][0], 0.6)
        self.assertAlmostEqual(result[0][1], -0.7)
        self.assertAlmostEqual(result[1][0], -0.2)
        self.assertAlmostEqual(result[1][1], 0.4)
        result, _ = evaluate_expression("solve([[2, 1], [1, -1]], [5, 1])")
        self.assertEqual(result, [2.0, 1.0])

    def test_linear_system_functions_support_complex_entries_and_pivoting(self):
        result, _ = evaluate_expression("inv([[1 + i]])")
        self.assertEqual(result, [[complex(0.5, -0.5)]])
        result, _ = evaluate_expression("solve([[0, 1], [2, 3]], [1, 5])")
        self.assertEqual(result, [1.0, 1.0])

    def test_matrix_functions_reject_invalid_inputs(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("shape([[1, 2], [3]])")
        self.assertEqual(
            str(error.exception),
            "Function 'shape' requires a rectangular matrix; row 2 has 1 item(s), expected 2.",
        )

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("rows([1, 2])")
        self.assertEqual(str(error.exception), "Function 'rows' expects argument to be a matrix of rows.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("dot([1, 2], [3])")
        self.assertEqual(str(error.exception), "Function 'dot' expects vectors of the same length.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("dot([1, [2]], [3, 4])")
        self.assertEqual(
            str(error.exception),
            "Function 'dot' expects first argument to be a vector of numbers.",
        )

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("matmul([[1, 2]], [[3, 4]])")
        self.assertEqual(
            str(error.exception),
            "Function 'matmul' requires the column count of the first matrix to match the row count of the second matrix.",
        )

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("det([[1, 2, 3], [4, 5, 6]])")
        self.assertEqual(str(error.exception), "Function 'det' requires a square matrix.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("inv([[1, 2], [2, 4]])")
        self.assertEqual(str(error.exception), "Function 'inv' requires a non-singular matrix.")

        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("solve([[1, 0], [0, 1]], [1])")
        self.assertEqual(
            str(error.exception),
            "Function 'solve' requires the second argument to have one value for each matrix row.",
        )

    def test_unary_operators_do_not_support_list_values(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("-[1, 2]")
        self.assertEqual(str(error.exception), "Unary operators do not support list values.")

    def test_si_prefix_literal(self):
        result, _ = evaluate_expression("10k + 25")
        self.assertEqual(result, 10025.0)

    def test_small_si_prefix_literal(self):
        result, _ = evaluate_expression("4.7m * 2")
        self.assertTrue(math.isclose(result, 0.0094))

    def test_extended_si_prefix_literal(self):
        result, _ = evaluate_expression("3f * 2")
        self.assertTrue(math.isclose(result, 6e-15))

    def test_degree_literal_is_converted_to_radians(self):
        result, _ = evaluate_expression("sin(90deg)")
        self.assertTrue(math.isclose(result, 1.0))

    def test_inverse_sine_returns_angle(self):
        context = EvaluationContext()
        result, context = evaluate_expression("asin(1)", context)
        self.assertTrue(math.isclose(result, math.pi / 2))
        self.assertEqual(context.entries[-1]["kind"], "angle")

    def test_atan2_returns_angle(self):
        context = EvaluationContext()
        result, context = evaluate_expression("atan2(1, 1)", context)
        self.assertTrue(math.isclose(result, math.pi / 4))
        self.assertEqual(context.entries[-1]["kind"], "angle")

    def test_radian_literal_is_used_directly(self):
        result, _ = evaluate_expression("sin(1.5707963267948966rad)")
        self.assertTrue(math.isclose(result, 1.0))

    def test_milliradian_literal_supports_si_prefix(self):
        result, _ = evaluate_expression("2mrad")
        self.assertEqual(result, 0.002)

    def test_pi_multiple_literal_is_supported(self):
        result, _ = evaluate_expression("2pi")
        self.assertTrue(math.isclose(result, 2 * math.pi))

    def test_pi_multiple_literal_preserves_angle_kind(self):
        context = EvaluationContext()
        result, context = evaluate_expression("0.5pi", context)
        self.assertTrue(math.isclose(result, math.pi / 2))
        self.assertEqual(context.entries[-1]["kind"], "angle")
        self.assertEqual(context.get_variable_kind("ans"), "angle")

    def test_angle_division_preserves_angle_kind(self):
        context = EvaluationContext()
        result, context = evaluate_expression("90deg / 2", context)
        self.assertTrue(math.isclose(result, math.pi / 4))
        self.assertEqual(context.entries[-1]["kind"], "angle")
        self.assertEqual(context.get_variable_kind("ans"), "angle")

    def test_angle_assignment_preserves_angle_kind(self):
        context = EvaluationContext()
        result, context = evaluate_expression("bearing = 45deg", context)
        self.assertTrue(math.isclose(result, math.pi / 4))
        self.assertTrue(math.isclose(context.get_variable("bearing"), math.pi / 4))
        self.assertEqual(context.get_variable_kind("bearing"), "angle")

    def test_second_literal_represents_duration(self):
        result, _ = evaluate_expression("90s")
        self.assertEqual(result, 90.0)

    def test_minute_literal_represents_duration(self):
        result, _ = evaluate_expression("45min")
        self.assertEqual(result, 2700.0)

    def test_compound_duration_literal_with_spaces(self):
        result, _ = evaluate_expression("1h 20m 30s")
        self.assertEqual(result, 4830.0)

    def test_compound_duration_literal_without_spaces(self):
        result, _ = evaluate_expression("1h20m30s")
        self.assertEqual(result, 4830.0)

    def test_duration_difference_preserves_duration_kind(self):
        context = EvaluationContext()
        result, context = evaluate_expression("12h 20m 12s - 6h 49m 39s", context)
        self.assertEqual(result, 19833.0)
        self.assertEqual(context.entries[-1]["kind"], "duration")
        self.assertEqual(context.get_variable_kind("ans"), "duration")

    def test_duration_assignment_preserves_duration_kind(self):
        context = EvaluationContext()
        result, context = evaluate_expression("work = 12h 20m 12s - 6h 49m 39s", context)
        self.assertEqual(result, 19833.0)
        self.assertEqual(context.get_variable("work"), 19833.0)
        self.assertEqual(context.get_variable_kind("work"), "duration")

    def test_short_minute_alias_requires_duration_context(self):
        result, _ = evaluate_expression("20m")
        self.assertEqual(result, 0.02)

    def test_imaginary_unit_variable(self):
        result, _ = evaluate_expression("i ^ 2")
        self.assertEqual(result, -1.0)

    def test_imaginary_number_literal(self):
        result, _ = evaluate_expression("2 + 3i")
        self.assertEqual(result, complex(2.0, 3.0))

    def test_imaginary_number_with_si_prefix_literal(self):
        result, _ = evaluate_expression("2ui")
        self.assertEqual(result, 2e-6j)

    def test_complex_expression(self):
        result, _ = evaluate_expression("(2 + 3i) * (1 - i)")
        self.assertEqual(result, complex(5.0, 1.0))

    def test_complex_builtin_function(self):
        result, _ = evaluate_expression("sqrt(-1)")
        self.assertEqual(result, 1j)

    def test_real_part_function(self):
        result, _ = evaluate_expression("re(2 + 3i)")
        self.assertEqual(result, 2.0)

    def test_imaginary_part_function(self):
        result, _ = evaluate_expression("im(2 + 3i)")
        self.assertEqual(result, 3.0)

    def test_complex_conjugate_function(self):
        result, _ = evaluate_expression("conj(2 + 3i)")
        self.assertEqual(result, complex(2.0, -3.0))

    def test_complex_argument_function(self):
        result, _ = evaluate_expression("arg(i)")
        self.assertTrue(math.isclose(result, math.pi / 2))

    def test_arg_function_preserves_angle_kind(self):
        context = EvaluationContext()
        result, context = evaluate_expression("arg(i)", context)
        self.assertTrue(math.isclose(result, math.pi / 2))
        self.assertEqual(context.entries[-1]["kind"], "angle")
        self.assertEqual(context.get_variable_kind("ans"), "angle")

    def test_degree_output_function(self):
        result, _ = evaluate_expression("deg(pi / 2)")
        self.assertEqual(result, 90.0)

    def test_dms_output_function(self):
        result, _ = evaluate_expression("dms(pi / 6)")
        self.assertEqual(result, '30deg 0\' 0"')

    def test_hms_output_function(self):
        result, _ = evaluate_expression("hms(4830)")
        self.assertEqual(result, "1h 20m 30s")

    def test_reciprocal_trigonometric_functions(self):
        result, _ = evaluate_expression("cot(45deg) + sec(60deg) + csc(30deg)")
        self.assertTrue(math.isclose(result, 5.0))

    def test_hyperbolic_functions(self):
        result, _ = evaluate_expression("cosh(0) + sinh(0) + tanh(0)")
        self.assertEqual(result, 1.0)

    def test_exponential_and_logarithmic_functions(self):
        result, _ = evaluate_expression("exp(2) - exp(2)")
        self.assertEqual(result, 0.0)
        result, _ = evaluate_expression("ln(e) + log10(1000) + log2(8)")
        self.assertEqual(result, 7.0)

    def test_floor_and_ceil_functions(self):
        result, _ = evaluate_expression("floor(3.9) + ceil(3.1)")
        self.assertEqual(result, 7.0)

    def test_reciprocal_trigonometric_zero_division_is_reported(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("cot(0)")
        self.assertEqual(str(error.exception), "Division by zero is not allowed.")

    def test_context_zero_tolerance_does_not_destroy_small_numeric_results(self):
        context = EvaluationContext()
        context.set_zero_tolerance(1e-12)
        result, context = evaluate_expression("3f * 2", context)
        self.assertTrue(math.isclose(result, 6e-15))
        self.assertTrue(math.isclose(context.get_variable("ans"), 6e-15))

    def test_ans_is_reused(self):
        context = EvaluationContext()
        first, context = evaluate_expression("10 / 2", context)
        second, context = evaluate_expression("ans + 3", context)
        self.assertEqual(first, 5.0)
        self.assertEqual(second, 8.0)
        self.assertEqual(context.history, [5.0, 8.0])
        self.assertEqual(
            context.entries,
            [
                {"expression": "10 / 2", "result": 5.0},
                {"expression": "ans + 3", "result": 8.0},
            ],
        )

    def test_ans_can_reuse_complex_results(self):
        context = EvaluationContext()
        first, context = evaluate_expression("sqrt(-1)", context)
        second, context = evaluate_expression("ans ^ 2", context)
        self.assertEqual(first, 1j)
        self.assertEqual(second, -1.0)
        self.assertEqual(context.history, [1j, -1.0])

    def test_program_with_newline_separated_statements(self):
        result, context = evaluate_expression("radius = 5\narea(r) = pi * r ^ 2\narea(radius)")
        self.assertEqual(result, 78.53981633974483)
        self.assertEqual(context.history, [5.0, 78.53981633974483])
        self.assertEqual(
            context.entries,
            [
                {
                    "expression": "radius = 5\narea(r) = pi * r ^ 2\narea(radius)",
                    "result": 78.53981633974483,
                }
            ],
        )

    def test_program_with_semicolon_separated_statements(self):
        result, context = evaluate_expression("2 + 2; ans * 3")
        self.assertEqual(result, 12.0)
        self.assertEqual(context.history, [4.0, 12.0])

    def test_multiline_parenthesized_expression(self):
        result, _ = evaluate_expression("(\n1 + 2\n) * 3")
        self.assertEqual(result, 9.0)

    def test_builtin_variables(self):
        result, _ = evaluate_expression("cos(0) + pi - pi")
        self.assertTrue(math.isclose(result, 1.0))

    def test_variable_assignment(self):
        context = EvaluationContext()
        result, context = evaluate_expression("mass = 12 / 3", context)
        reused, context = evaluate_expression("mass + 2", context)
        self.assertEqual(result, 4.0)
        self.assertEqual(reused, 6.0)
        self.assertEqual(context.get_variable("mass"), 4.0)

    def test_user_variable_can_be_deleted(self):
        context = EvaluationContext()
        _, context = evaluate_expression("mass = 12 / 3", context)
        context.delete_variable("mass")
        self.assertEqual(context.user_variables(), {})
        with self.assertRaises(EvaluationError) as error:
            context.get_variable("mass")
        self.assertEqual(str(error.exception), "Unknown variable: mass")

    def test_protected_variable_cannot_be_assigned(self):
        with self.assertRaises(EvaluationError):
            evaluate_expression("pi = 4")

    def test_imaginary_unit_cannot_be_assigned(self):
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("i = 4")
        self.assertEqual(str(error.exception), "Protected variable cannot be assigned: i")

    def test_protected_variable_cannot_be_deleted(self):
        context = EvaluationContext()
        with self.assertRaises(EvaluationError) as error:
            context.delete_variable("pi")
        self.assertEqual(str(error.exception), "Protected variable cannot be deleted: pi")

    def test_division_by_zero(self):
        with self.assertRaises(EvaluationError):
            evaluate_expression("5 / 0")

    def test_user_function_definition_and_call(self):
        context = EvaluationContext()
        result, context = evaluate_expression("square(x) = x ^ 2", context)
        called, context = evaluate_expression("square(4)", context)
        self.assertEqual(result, "Defined square(x)")
        self.assertEqual(called, 16.0)
        self.assertEqual(context.history, [16.0])
        self.assertEqual(context.user_functions()["square"].signature(), "square(x)")

    def test_user_function_can_be_deleted(self):
        context = EvaluationContext()
        _, context = evaluate_expression("square(x) = x ^ 2", context)
        context.delete_function("square")
        self.assertEqual(context.user_functions(), {})
        with self.assertRaises(EvaluationError) as error:
            evaluate_expression("square(4)", context)
        self.assertEqual(
            str(error.exception),
            "Unknown function: square. Did you mean 'sqrt'?",
        )

    def test_reset_user_state_clears_runtime_state(self):
        context = EvaluationContext()
        _, context = evaluate_expression("mass = 12 / 3", context)
        _, context = evaluate_expression("square(x) = x ^ 2", context)
        _, context = evaluate_expression("square(mass)", context)
        context.reset_user_state()
        self.assertEqual(context.user_variables(), {})
        self.assertEqual(context.user_functions(), {})
        self.assertEqual(context.history, [])
        self.assertEqual(context.entries, [])
        self.assertEqual(context.get_variable("ans"), 0.0)

    def test_user_function_can_use_global_variables(self):
        context = EvaluationContext()
        _, context = evaluate_expression("scale = 3", context)
        _, context = evaluate_expression("scale_by(x) = x * scale", context)
        result, context = evaluate_expression("scale_by(5)", context)
        self.assertEqual(result, 15.0)

    def test_user_function_argument_count_validation(self):
        context = EvaluationContext()
        _, context = evaluate_expression("inc(x) = x + 1", context)
        with self.assertRaises(EvaluationError) as context_manager:
            evaluate_expression("inc(1, 2)", context)
        self.assertEqual(
            str(context_manager.exception),
            "Function 'inc' expects 1 argument(s), got 2.",
        )

    def test_builtin_function_cannot_be_redefined(self):
        with self.assertRaises(EvaluationError) as context:
            evaluate_expression("sin(x) = x")
        self.assertEqual(
            str(context.exception),
            "Protected function cannot be redefined: sin",
        )

    def test_duplicate_function_parameters_are_rejected(self):
        with self.assertRaises(EvaluationError) as context:
            evaluate_expression("pair(x, x) = x")
        self.assertEqual(
            str(context.exception),
            "Duplicate parameter in function definition: x",
        )

    def test_unknown_function(self):
        with self.assertRaises(EvaluationError) as context:
            evaluate_expression("sqt(9)")
        self.assertEqual(
            str(context.exception),
            "Unknown function: sqt. Did you mean 'sqrt'?",
        )

    def test_unknown_variable_suggestion(self):
        with self.assertRaises(EvaluationError) as context:
            evaluate_expression("pn + 1")
        self.assertEqual(
            str(context.exception),
            "Unknown variable: pn. Did you mean 'pi'?",
        )

    def test_invalid_syntax(self):
        with self.assertRaises(ParseError) as context:
            evaluate_expression("1 +")
        self.assertEqual(str(context.exception), "Unexpected end of expression.")

    def test_trailing_semicolon_requires_more_input(self):
        with self.assertRaises(IncompleteInputError) as context:
            parse_input("radius = 5;")
        self.assertEqual(str(context.exception), "Expected another statement after ';'.")


if __name__ == "__main__":
    unittest.main()
