import unittest

from slowcrunch.runtime.context import EvaluationContext
from slowcrunch.tui.repl import _completion_candidates


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


if __name__ == "__main__":
    unittest.main()
