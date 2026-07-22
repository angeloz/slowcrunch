import unittest

from slowcrunch.core.errors import EvaluationError, SessionError
from slowcrunch.runtime.context import EvaluationContext
from slowcrunch.tui.repl import (
    DisplaySettings,
    SessionState,
    _apply_variable_snapshot,
    _completion_candidates,
    _ensure_clean_session,
    _help_lines,
    _history_lines,
    _history_replay_entry,
    _list_slice_lines,
    _requires_continuation,
    _status_lines,
    _variable_value_lines,
)


class SlowCrunchReplCompletionTest(unittest.TestCase):
    def test_function_completion_adds_open_parenthesis(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "sq")
        self.assertEqual(matches, ["sqrt("])

    def test_variable_completion_includes_builtins_and_user_variables(self):
        context = EvaluationContext()
        context.set_variable("radius", 5.0)
        matches = _completion_candidates(context, "r")
        self.assertIn("radius", matches)
        self.assertIn("re(", matches)

    def test_expression_completion_includes_keywords(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "q")
        self.assertEqual(matches, ["quit"])

    def test_requires_continuation_for_trailing_semicolon(self):
        self.assertTrue(_requires_continuation("radius = 5;"))

    def test_requires_continuation_for_open_parenthesis(self):
        self.assertTrue(_requires_continuation("(\n1 + 2"))

    def test_complete_multiline_program_does_not_require_continuation(self):
        self.assertFalse(_requires_continuation("radius = 5;\narea(r) = pi * r ^ 2;\narea(radius)"))

    def test_command_completion_filters_repl_commands(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":h", ":h", 0)
        self.assertEqual(matches, [":head", ":help", ":history"])

    def test_angles_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":an", ":an", 0)
        self.assertEqual(matches, [":angles"])

    def test_tolerance_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":to", ":to", 0)
        self.assertEqual(matches, [":tolerance"])

    def test_angle_mode_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "dm", ":angles dm", 8)
        self.assertEqual(matches, ["dms"])

    def test_format_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":fo", ":fo", 0)
        self.assertEqual(matches, [":format"])

    def test_format_mode_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "sc", ":format sc", 8)
        self.assertEqual(matches, ["scientific"])

    def test_functions_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":f", ":f", 0)
        self.assertEqual(matches, [":format", ":functions"])

    def test_head_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":hea", ":hea", 0)
        self.assertEqual(matches, [":head"])

    def test_show_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":sho", ":sho", 0)
        self.assertEqual(matches, [":show"])

    def test_tail_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":ta", ":ta", 0)
        self.assertEqual(matches, [":tail"])

    def test_new_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":ne", ":ne", 0)
        self.assertEqual(matches, [":new"])

    def test_rename_session_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":rename", ":rename", 0)
        self.assertEqual(matches, [":rename-session"])

    def test_status_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":st", ":st", 0)
        self.assertEqual(matches, [":status"])

    def test_clear_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":cl", ":cl", 0)
        self.assertEqual(matches, [":clear"])

    def test_delete_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":de", ":de", 0)
        self.assertEqual(matches, [":delete"])

    def test_reset_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":re", ":re", 0)
        self.assertIn(":reset", matches)

    def test_save_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":sa", ":sa", 0)
        self.assertIn(":save", matches)

    def test_saveas_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":savea", ":savea", 0)
        self.assertEqual(matches, [":saveas"])

    def test_sessions_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":se", ":se", 0)
        self.assertEqual(matches, [":sessions"])

    def test_command_completion_does_not_mix_expression_names(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "s")
        self.assertIn("sin(", matches)
        self.assertIn("sqrt(", matches)
        self.assertNotIn(":history", matches)

    def test_help_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":he", ":he", 0)
        self.assertEqual(matches, [":head", ":help"])

    def test_help_topic_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "fu", ":help fu", 6)
        self.assertEqual(matches, ["functions"])

    def test_delete_target_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "fu", ":delete fu", 8)
        self.assertEqual(matches, ["function"])

    def test_delete_variable_name_is_completable(self):
        context = EvaluationContext()
        context.set_variable("radius", 5.0)
        matches = _completion_candidates(context, "ra", ":delete var ra", 12)
        self.assertEqual(matches, ["radius"])

    def test_delete_function_name_is_completable(self):
        context = EvaluationContext()
        context.set_function("area", ["radius"], None)
        matches = _completion_candidates(context, "ar", ":delete function ar", 17)
        self.assertEqual(matches, ["area"])

    def test_delete_session_name_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(
            context,
            "de",
            ":delete session de",
            16,
            session_names=["demo", "weekly"],
        )
        self.assertEqual(matches, ["demo"])

    def test_load_session_name_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(
            context,
            "de",
            ":load de",
            6,
            session_names=["demo", "weekly"],
        )
        self.assertEqual(matches, ["demo"])

    def test_import_vars_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":import", ":import", 0)
        self.assertEqual(matches, [":import-vars"])

    def test_load_vars_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":load-v", ":load-v", 0)
        self.assertEqual(matches, [":load-vars"])

    def test_save_vars_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":save-v", ":save-v", 0)
        self.assertEqual(matches, [":save-vars"])

    def test_show_variable_name_is_completable(self):
        context = EvaluationContext()
        context.set_variable("values", [1.0, 2.0, 3.0])
        matches = _completion_candidates(context, "va", ":show va", 6)
        self.assertEqual(matches, ["values"])

    def test_head_variable_name_is_completable(self):
        context = EvaluationContext()
        context.set_variable("values", [1.0, 2.0, 3.0])
        matches = _completion_candidates(context, "va", ":head va", 6)
        self.assertEqual(matches, ["values"])

    def test_tail_variable_name_is_completable(self):
        context = EvaluationContext()
        context.set_variable("values", [1.0, 2.0, 3.0])
        matches = _completion_candidates(context, "va", ":tail va", 6)
        self.assertEqual(matches, ["values"])

    def test_user_defined_function_is_completable(self):
        context = EvaluationContext()
        context.set_function("area", ["radius"], None)
        matches = _completion_candidates(context, "ar")
        self.assertIn("area(", matches)
        self.assertIn("arg(", matches)

    def test_general_help_mentions_help_topics(self):
        lines = _help_lines()
        self.assertIn(":angles [MODE] Show or change the angle output mode.", lines)
        self.assertIn(":format [MODE] Show or change the numeric output mode.", lines)
        self.assertIn(":head NAME [COUNT] Show the first items of a list variable.", lines)
        self.assertIn(":tolerance [VALUE] Show or change the zero tolerance.", lines)
        self.assertIn(":history [text|!index] Show, filter, or replay history.", lines)
        self.assertIn(":import-vars PATH [FORMAT] Merge variables from a JSON or CSV file.", lines)
        self.assertIn(":load-vars PATH [FORMAT] Replace user variables from a JSON or CSV file.", lines)
        self.assertIn(":save-vars PATH [FORMAT] Write user variables to a JSON or CSV file.", lines)
        self.assertIn(":show NAME Show a variable or structured result with TUI formatting.", lines)
        self.assertIn(":tail NAME [COUNT] Show the last items of a list variable.", lines)
        self.assertIn(
            "Help topics: angles, basics, clear, delete, format, functions, head, history, new, reset, sessions, show, status, tail, tolerance, vars",
            lines,
        )
        self.assertIn("  :help angles", lines)
        self.assertIn("  :help delete", lines)
        self.assertIn("  :help format", lines)
        self.assertIn("  :help functions", lines)
        self.assertIn("  :help show", lines)
        self.assertIn("  :help sessions", lines)
        self.assertIn("  :help status", lines)
        self.assertIn("  :help tolerance", lines)

    def test_angles_help_explains_available_modes(self):
        lines = _help_lines("angles")
        self.assertIn("Available modes: deg, dms, rad.", lines)
        self.assertIn("This affects angle-typed results such as 90deg / 2 or arg(i).", lines)
        self.assertIn("Use compact pi-multiples such as 2pi or 0.5pi for angle-typed radian input.", lines)
        self.assertIn("Use 360deg or 2 * 180deg when you want 2*pi as an angle-typed value.", lines)
        self.assertIn("Use 2 * pi when you only need the numeric radian value.", lines)
        self.assertIn("  :angles rad", lines)
        self.assertIn("  2pi", lines)
        self.assertIn("  360deg", lines)

    def test_clear_help_explains_screen_only_behavior(self):
        lines = _help_lines("clear")
        self.assertIn("Use :clear to clear the visible terminal screen.", lines)

    def test_delete_help_explains_supported_targets(self):
        lines = _help_lines("delete")
        self.assertIn("Supported targets are var, function, and session.", lines)
        self.assertIn("  :delete session demo", lines)

    def test_functions_help_explains_definition_syntax(self):
        lines = _help_lines("functions")
        self.assertIn("Several built-in functions accept complex arguments.", lines)
        self.assertIn("Supported built-in functions are grouped by category below.", lines)
        self.assertIn("Statistics functions currently use list arguments such as [1, 2, 3].", lines)
        self.assertIn("Complex values are supported by sum, mean, dispersion, covariance, and correlation statistics.", lines)
        self.assertIn("Complex variance and covariance use conjugate products; ordered statistics and linreg require real lists.", lines)
        self.assertIn("Linear algebra functions use vectors such as [1, 2] and matrices such as [[1, 2], [3, 4]].", lines)
        self.assertIn("Use det(A), inv(A), or solve(A, b) for square matrices and linear systems.", lines)
        self.assertIn("Inverse trigonometric functions and arg return angle-typed results and follow :angles.", lines)
        self.assertIn(
            "Define user functions with the form name(param1, param2) = expression.",
            lines,
        )
        self.assertIn(
            "Trigonometric: sin, cos, tan, cot, sec, csc",
            lines,
        )
        self.assertIn(
            "Inverse trigonometric: asin, acos, atan, atan2, acot, asec, acsc, arg",
            lines,
        )
        self.assertIn("Hyperbolic: sinh, cosh, tanh, coth, sech, csch", lines)
        self.assertIn("Inverse hyperbolic: asinh, acosh, atanh", lines)
        self.assertIn("Exponential and logarithmic: exp, ln, log, log10, log2, sqrt", lines)
        self.assertIn("Complex and utility: abs, floor, ceil, re, im, conj", lines)
        self.assertIn(
            "Statistics: len, sum, min, max, mean, median, mode, variance, stdev, sample_variance, sample_stdev, cov, sample_cov, corr, linreg",
            lines,
        )
        self.assertIn("Combinatorics: fact, perm, comb", lines)
        self.assertIn("Linear algebra: shape, rows, cols, transpose, dot, matmul, det, inv, solve", lines)
        self.assertIn("Formatting helpers: deg, dms, hms", lines)
        self.assertIn("  asin(1)", lines)
        self.assertIn("  atan2(1, 1)", lines)
        self.assertIn("  cot(45deg)", lines)
        self.assertIn("  sinh(1)", lines)
        self.assertIn("  exp(2)", lines)
        self.assertIn("  len([1, 2, 3])", lines)
        self.assertIn("  sum([1, 2, 3])", lines)
        self.assertIn("  mean([1, 2, 3])", lines)
        self.assertIn("  median([1, 2, 3, 4])", lines)
        self.assertIn("  mode([1, 1, 2])", lines)
        self.assertIn("  variance([1, 2, 3])", lines)
        self.assertIn("  sample_stdev([1, 2, 3])", lines)
        self.assertIn("  cov([1, 2, 3], [2, 4, 6])", lines)
        self.assertIn("  corr([1, 2, 3], [2, 4, 6])", lines)
        self.assertIn("  linreg([1, 2, 3], [2, 4, 6])", lines)
        self.assertIn("  fact(5)", lines)
        self.assertIn("  perm(5, 2)", lines)
        self.assertIn("  comb(5, 2)", lines)
        self.assertIn("  deg(pi / 2)", lines)
        self.assertIn("  dms(pi / 6)", lines)
        self.assertIn("  hms(4830)", lines)
        self.assertIn("  :functions", lines)

    def test_format_help_explains_available_modes(self):
        lines = _help_lines("format")
        self.assertIn("Available modes: plain, scientific, engineering, si.", lines)
        self.assertIn("Use :angles for angle-specific output policy.", lines)
        self.assertIn("Use :tolerance for near-zero normalization.", lines)
        self.assertIn("SI uses engineering steps with SI prefixes, such as 12k or 220u.", lines)
        self.assertIn("  :format si", lines)

    def test_tolerance_help_explains_zero_threshold(self):
        lines = _help_lines("tolerance")
        self.assertIn("Values with absolute magnitude below the tolerance are normalized to zero.", lines)
        self.assertIn("Use a non-negative floating-point value, such as 1e-12.", lines)
        self.assertIn("  :tolerance 1e-12", lines)

    def test_reset_help_explains_in_memory_reset(self):
        lines = _help_lines("reset")
        self.assertIn("Use :reset to clear the current in-memory session.", lines)
        self.assertIn("Saved session files are not deleted.", lines)
        self.assertIn("use :reset --force or save first.", " ".join(lines).lower())

    def test_new_help_mentions_force_for_unsaved_changes(self):
        lines = _help_lines("new")
        self.assertIn("Use :new to start a fresh empty session.", lines)
        self.assertIn("use :new --force or save first.", " ".join(lines).lower())

    def test_history_help_mentions_filter_and_replay(self):
        lines = _help_lines("history")
        self.assertIn("Use :history text to filter entries by expression or rendered result.", lines)
        self.assertIn("Use :history !index to replay a previous entry.", lines)
        self.assertIn("  :history !3", lines)

    def test_show_help_explains_structured_rendering(self):
        lines = _help_lines("show")
        self.assertIn("Use :show name to render a variable with the same structured formatting used by the REPL.", lines)
        self.assertIn("  :show ans", lines)

    def test_head_help_explains_default_count(self):
        lines = _help_lines("head")
        self.assertIn("If count is omitted, the default is 5.", lines)
        self.assertIn("  :head values 3", lines)

    def test_tail_help_explains_default_count(self):
        lines = _help_lines("tail")
        self.assertIn("If count is omitted, the default is 5.", lines)
        self.assertIn("  :tail values 3", lines)

    def test_status_help_mentions_dirty_state(self):
        lines = _help_lines("status")
        self.assertIn("The status includes the active session name, last save time, dirty state, numeric format mode, angle mode, zero tolerance, and object counts.", lines)

    def test_vars_help_explains_assignment_syntax(self):
        lines = _help_lines("vars")
        self.assertIn("Assign user variables with the form name = expression.", lines)
        self.assertIn("Protected names such as ans, pi, e, and i cannot be reassigned.", lines)
        self.assertIn("Use :save-vars path [json|csv] to export user variables to a file.", lines)
        self.assertIn("Use :load-vars path [json|csv] [--force] to replace current user variables from a file.", lines)
        self.assertIn("Use :import-vars path [json|csv] to merge variables from a file into the current session.", lines)
        self.assertIn("  :vars", lines)
        self.assertIn("  :save-vars vars.json", lines)
        self.assertIn("  :load-vars vars.csv --force", lines)
        self.assertIn("  :import-vars vars.json", lines)

    def test_basics_help_mentions_imaginary_unit(self):
        lines = _help_lines("basics")
        self.assertIn("Built-in constants include pi, e, and i.", lines)
        self.assertIn("Numbers can use scientific notation such as 1.2e6.", lines)
        self.assertIn("Numbers can use SI prefixes such as 10k, 1M, 220u, or 3f.", lines)
        self.assertIn("Angles can use explicit units such as 90deg, 1.5rad, or 2mrad.", lines)
        self.assertIn("Angle arithmetic keeps angle-style output when the result stays an angle.", lines)
        self.assertIn("Use :angles to choose whether angle results are shown as deg, dms, or rad.", lines)
        self.assertIn("Use compact pi-multiples such as 2pi or 0.5pi for angle-typed radian input.", lines)
        self.assertIn("Use 360deg or 2 * 180deg when you want 2*pi to keep angle-style output.", lines)
        self.assertIn("Durations can use explicit units such as 1h 20m 30s, 45min, or 90s.", lines)
        self.assertIn("Duration arithmetic keeps duration-style output when the result stays a duration.", lines)
        self.assertIn("Use :tolerance to control when very small values are normalized to zero.", lines)
        self.assertIn("Use deg(x), dms(x), and hms(x) to format angles and durations explicitly.", lines)
        self.assertIn("  2 + 3i", lines)
        self.assertIn("  10k + 25", lines)
        self.assertIn("  sin(90deg)", lines)
        self.assertIn("  2pi", lines)
        self.assertIn("  360deg", lines)
        self.assertIn("  90deg / 2", lines)
        self.assertIn("  1h 20m 30s", lines)
        self.assertIn("  12h 20m 12s - 6h 49m 39s", lines)
        self.assertIn("  deg(pi / 2)", lines)
        self.assertIn("  dms(pi / 6)", lines)
        self.assertIn("  hms(4830)", lines)
        self.assertIn("  sqrt(-1)", lines)

    def test_unknown_help_topic_lists_available_topics(self):
        lines = _help_lines("unknown")
        self.assertEqual(lines[0], "Unknown help topic 'unknown'.")
        self.assertEqual(
            lines[1],
            "Available topics: angles, basics, clear, delete, format, functions, head, history, new, reset, sessions, show, status, tail, tolerance, vars",
        )

    def test_sessions_help_explains_save_and_load(self):
        lines = _help_lines("sessions")
        self.assertIn("Use :save [name] to store the current session as JSON.", lines)
        self.assertIn("Use :saveas name to save under a new explicit name.", lines)
        self.assertIn("Use :status to inspect the current session state.", lines)
        self.assertIn("Use :rename-session name to rename the current saved session on disk.", lines)
        self.assertIn("  :load demo", lines)

    def test_status_lines_for_unsaved_session(self):
        context = EvaluationContext()
        lines = _status_lines(context, SessionState(), DisplaySettings())
        self.assertEqual(lines[0], "Session: <unsaved>")
        self.assertEqual(lines[1], "Saved at: never")
        self.assertEqual(lines[2], "Modified: no")
        self.assertEqual(lines[3], "Format: plain")
        self.assertEqual(lines[4], "Angles: deg")
        self.assertEqual(lines[5], "Zero tolerance: 1e-12")

    def test_status_lines_for_saved_dirty_session(self):
        context = EvaluationContext()
        context.set_variable("radius", 5.0)
        context.set_function("area", ["r"], None)
        context.set_zero_tolerance(1e-12)
        state = SessionState("demo", "2026-07-20T13:00:00+02:00", True)
        lines = _status_lines(context, state, DisplaySettings("si", "rad"))
        self.assertEqual(lines[0], "Session: demo")
        self.assertEqual(lines[1], "Saved at: 2026-07-20T13:00:00+02:00")
        self.assertEqual(lines[2], "Modified: yes")
        self.assertEqual(lines[3], "Format: si")
        self.assertEqual(lines[4], "Angles: rad")
        self.assertEqual(lines[5], "Zero tolerance: 1e-12")
        self.assertEqual(lines[6], "User variables: 1")
        self.assertEqual(lines[7], "User functions: 1")

    def test_history_lines_show_all_entries(self):
        context = EvaluationContext()
        context.record_entry("radius = 5", 5.0)
        context.record_entry("area(r) = pi * r ^ 2", "Defined area(r)")
        lines = _history_lines(context, DisplaySettings())
        self.assertEqual(lines[0], "1: radius = 5 = 5.0")
        self.assertEqual(lines[1], "2: area(r) = pi * r ^ 2 = Defined area(r)")

    def test_history_lines_render_short_list_with_summary(self):
        context = EvaluationContext()
        context.record_entry("values", [1.0, 2.0, 3.0])
        lines = _history_lines(context, DisplaySettings())
        self.assertEqual(lines, ["1: values = list[3] [1.0, 2.0, 3.0]"])

    def test_history_lines_render_long_list_multiline(self):
        context = EvaluationContext()
        context.record_entry("values", [1.0, 2.0, 3.0, 4.0, 5.0])
        lines = _history_lines(context, DisplaySettings())
        self.assertEqual(lines[0], "1: values = list[5]")
        self.assertEqual(lines[1], "     [0] 1.0")
        self.assertEqual(lines[2], "     [1] 2.0")
        self.assertEqual(lines[5], "     [4] 5.0")

    def test_history_lines_render_linreg_result_with_labels(self):
        context = EvaluationContext()
        context.record_entry("linreg([1, 2, 3], [2, 4, 6])", [2.0, 0.0])
        lines = _history_lines(context, DisplaySettings())
        self.assertEqual(
            lines,
            ["1: linreg([1, 2, 3], [2, 4, 6]) = linreg[slope=2.0, intercept=0.0]"],
        )

    def test_variable_value_lines_render_list_with_label_ready_output(self):
        context = EvaluationContext()
        context.set_variable("values", [1.0, 2.0, 3.0, 4.0, 5.0])
        lines = _variable_value_lines(context, DisplaySettings(), "values")
        self.assertEqual(lines[0], "list[5]")
        self.assertEqual(lines[1], "  [0] 1.0")

    def test_variable_value_lines_render_ans_linreg_result(self):
        context = EvaluationContext()
        context.variables["ans"] = [2.0, 0.0]
        lines = _variable_value_lines(
            context,
            DisplaySettings(),
            "ans",
            "linreg([1, 2, 3], [2, 4, 6])",
        )
        self.assertEqual(lines, ["linreg[slope=2.0, intercept=0.0]"])

    def test_variable_value_lines_render_ans_linreg_result_from_last_history_entry(self):
        context = EvaluationContext()
        context.record_entry("linreg([1, 2, 3], [2, 4, 6])", [2.0, 0.0])
        context.variables["ans"] = [2.0, 0.0]
        lines = _variable_value_lines(context, DisplaySettings(), "ans")
        self.assertEqual(lines, ["linreg[slope=2.0, intercept=0.0]"])

    def test_list_slice_lines_render_head_subset(self):
        context = EvaluationContext()
        context.set_variable("values", [1.0, 2.0, 3.0, 4.0, 5.0])
        lines = _list_slice_lines(context, DisplaySettings(), "values", 3)
        self.assertEqual(lines, ["list[3] [1.0, 2.0, 3.0]"])

    def test_list_slice_lines_render_tail_subset(self):
        context = EvaluationContext()
        context.set_variable("values", [1.0, 2.0, 3.0, 4.0, 5.0])
        lines = _list_slice_lines(context, DisplaySettings(), "values", 2, from_tail=True)
        self.assertEqual(lines, ["list[2] [4.0, 5.0]"])

    def test_list_slice_lines_reject_non_list_variable(self):
        context = EvaluationContext()
        context.set_variable("radius", 5.0)
        with self.assertRaises(SessionError) as error:
            _list_slice_lines(context, DisplaySettings(), "radius", 2)
        self.assertEqual(str(error.exception), "Variable 'radius' is not a list.")

    def test_apply_variable_snapshot_can_merge_variables(self):
        context = EvaluationContext()
        context.set_variable("radius", 5.0)
        _apply_variable_snapshot(
            context,
            {"values": [1.0, 2.0, 3.0]},
            {},
            replace=False,
        )
        self.assertEqual(context.get_variable("radius"), 5.0)
        self.assertEqual(context.get_variable("values"), [1.0, 2.0, 3.0])

    def test_apply_variable_snapshot_can_replace_variables(self):
        context = EvaluationContext()
        context.set_variable("radius", 5.0)
        _apply_variable_snapshot(
            context,
            {"values": [1.0, 2.0, 3.0]},
            {},
            replace=True,
        )
        with self.assertRaises(EvaluationError):
            context.get_variable("radius")
        self.assertEqual(context.get_variable("values"), [1.0, 2.0, 3.0])

    def test_apply_variable_snapshot_rejects_protected_names(self):
        context = EvaluationContext()
        with self.assertRaises(SessionError) as error:
            _apply_variable_snapshot(context, {"ans": 5.0}, {}, replace=False)
        self.assertEqual(str(error.exception), "Protected variable cannot be imported: ans")

    def test_history_lines_filter_entries(self):
        context = EvaluationContext()
        context.record_entry("radius = 5", 5.0)
        context.record_entry("area(r) = pi * r ^ 2", "Defined area(r)")
        lines = _history_lines(context, DisplaySettings(), "area")
        self.assertEqual(lines, ["2: area(r) = pi * r ^ 2 = Defined area(r)"])

    def test_history_lines_format_complex_values(self):
        context = EvaluationContext()
        context.record_entry("sqrt(-1)", 1j)
        lines = _history_lines(context, DisplaySettings())
        self.assertEqual(lines, ["1: sqrt(-1) = i"])

    def test_history_lines_format_negative_imaginary_values(self):
        context = EvaluationContext()
        context.record_entry("conj(i)", -1j)
        lines = _history_lines(context, DisplaySettings())
        self.assertEqual(lines, ["1: conj(i) = -i"])

    def test_history_lines_filter_complex_values_by_rendered_form(self):
        context = EvaluationContext()
        context.record_entry("sqrt(-1)", 1j)
        lines = _history_lines(context, DisplaySettings(), "i")
        self.assertEqual(lines, ["1: sqrt(-1) = i"])

    def test_history_lines_report_missing_filter_match(self):
        context = EvaluationContext()
        context.record_entry("radius = 5", 5.0)
        lines = _history_lines(context, DisplaySettings(), "mass")
        self.assertEqual(lines, ["No history entries matching 'mass'."])

    def test_history_lines_use_active_format_mode(self):
        context = EvaluationContext()
        context.record_entry("10000", 10000.0)
        lines = _history_lines(context, DisplaySettings("si"))
        self.assertEqual(lines, ["1: 10000 = 10k"])

    def test_history_lines_render_duration_entries_as_durations(self):
        context = EvaluationContext()
        context.record_entry("12h 20m 12s - 6h 49m 39s", 19833.0, "duration")
        lines = _history_lines(context, DisplaySettings())
        self.assertEqual(lines, ["1: 12h 20m 12s - 6h 49m 39s = 5h 30m 33s"])

    def test_history_lines_use_zero_tolerance_for_near_zero_results(self):
        context = EvaluationContext()
        context.set_zero_tolerance(1e-12)
        context.record_entry("sin(360deg)", -2.4492935982947064e-16)
        lines = _history_lines(context, DisplaySettings())
        self.assertEqual(lines, ["1: sin(360deg) = 0.0"])

    def test_history_lines_render_angle_entries_as_angles(self):
        context = EvaluationContext()
        context.record_entry("90deg / 2", 0.7853981633974483, "angle")
        lines = _history_lines(context, DisplaySettings())
        self.assertEqual(lines, ["1: 90deg / 2 = 45deg"])

    def test_history_lines_render_angle_entries_in_dms_mode(self):
        context = EvaluationContext()
        context.record_entry("90deg / 2", 0.7853981633974483, "angle")
        lines = _history_lines(context, DisplaySettings(angle_mode="dms"))
        self.assertEqual(lines, ['1: 90deg / 2 = 45deg 0\' 0"'])

    def test_history_replay_entry_returns_indexed_entry(self):
        context = EvaluationContext()
        context.record_entry("radius = 5", 5.0)
        entry_index, entry = _history_replay_entry(context, "!1")
        self.assertEqual(entry_index, 1)
        self.assertEqual(entry["expression"], "radius = 5")

    def test_history_replay_entry_rejects_invalid_token(self):
        context = EvaluationContext()
        context.record_entry("radius = 5", 5.0)
        with self.assertRaises(SessionError) as error:
            _history_replay_entry(context, "radius")
        self.assertEqual(
            str(error.exception),
            "History replay requires !index, such as :history !3.",
        )

    def test_history_replay_entry_rejects_unknown_index(self):
        context = EvaluationContext()
        context.record_entry("radius = 5", 5.0)
        with self.assertRaises(SessionError) as error:
            _history_replay_entry(context, "!3")
        self.assertEqual(str(error.exception), "Unknown history entry: 3")

    def test_ensure_clean_session_raises_when_dirty(self):
        with self.assertRaises(SessionError) as error:
            _ensure_clean_session(SessionState("demo", None, True), ":load", False)
        self.assertEqual(
            str(error.exception),
            "Current session has unsaved changes. Use :load --force or :save first.",
        )

    def test_ensure_clean_session_allows_force(self):
        _ensure_clean_session(SessionState("demo", None, True), ":load", True)


if __name__ == "__main__":
    unittest.main()
