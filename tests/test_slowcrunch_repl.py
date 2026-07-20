import unittest

from slowcrunch.runtime.context import EvaluationContext
from slowcrunch.tui.repl import _completion_candidates, _help_lines


class SlowCrunchReplCompletionTest(unittest.TestCase):
    def test_function_completion_adds_open_parenthesis(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "sq")
        self.assertEqual(matches, ["sqrt("])

    def test_variable_completion_includes_builtins_and_user_variables(self):
        context = EvaluationContext()
        context.set_variable("radius", 5.0)
        matches = _completion_candidates(context, "r")
        self.assertEqual(matches, ["radius"])

    def test_expression_completion_includes_keywords(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "q")
        self.assertEqual(matches, ["quit"])

    def test_command_completion_filters_repl_commands(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":h", ":h", 0)
        self.assertEqual(matches, [":help", ":history"])

    def test_functions_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":f", ":f", 0)
        self.assertEqual(matches, [":functions"])

    def test_save_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":sa", ":sa", 0)
        self.assertEqual(matches, [":save"])

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
        self.assertEqual(matches, [":help"])

    def test_help_topic_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, "fu", ":help fu", 6)
        self.assertEqual(matches, ["functions"])

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

    def test_user_defined_function_is_completable(self):
        context = EvaluationContext()
        context.set_function("area", ["radius"], None)
        matches = _completion_candidates(context, "ar")
        self.assertEqual(matches, ["area("])

    def test_general_help_mentions_help_topics(self):
        lines = _help_lines()
        self.assertIn("Help topics: basics, functions, history, sessions, vars", lines)
        self.assertIn("  :help functions", lines)
        self.assertIn("  :help sessions", lines)

    def test_functions_help_explains_definition_syntax(self):
        lines = _help_lines("functions")
        self.assertIn(
            "Define user functions with the form name(param1, param2) = expression.",
            lines,
        )
        self.assertIn("  :functions", lines)

    def test_vars_help_explains_assignment_syntax(self):
        lines = _help_lines("vars")
        self.assertIn("Assign user variables with the form name = expression.", lines)
        self.assertIn("  :vars", lines)

    def test_unknown_help_topic_lists_available_topics(self):
        lines = _help_lines("unknown")
        self.assertEqual(lines[0], "Unknown help topic 'unknown'.")
        self.assertEqual(lines[1], "Available topics: basics, functions, history, sessions, vars")

    def test_sessions_help_explains_save_and_load(self):
        lines = _help_lines("sessions")
        self.assertIn("Use :save [name] to store the current session as JSON.", lines)
        self.assertIn("  :load demo", lines)


if __name__ == "__main__":
    unittest.main()
