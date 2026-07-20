import unittest

from slowcrunch.core.errors import SessionError
from slowcrunch.runtime.context import EvaluationContext
from slowcrunch.tui.repl import (
    SessionState,
    _completion_candidates,
    _ensure_clean_session,
    _help_lines,
    _requires_continuation,
    _status_lines,
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
        self.assertEqual(matches, ["radius"])

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
        self.assertEqual(matches, [":help", ":history"])

    def test_functions_command_is_completable(self):
        context = EvaluationContext()
        matches = _completion_candidates(context, ":f", ":f", 0)
        self.assertEqual(matches, [":functions"])

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
        self.assertEqual(matches, [":help"])

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

    def test_user_defined_function_is_completable(self):
        context = EvaluationContext()
        context.set_function("area", ["radius"], None)
        matches = _completion_candidates(context, "ar")
        self.assertEqual(matches, ["area("])

    def test_general_help_mentions_help_topics(self):
        lines = _help_lines()
        self.assertIn(
            "Help topics: basics, clear, delete, functions, history, new, reset, sessions, status, vars",
            lines,
        )
        self.assertIn("  :help delete", lines)
        self.assertIn("  :help functions", lines)
        self.assertIn("  :help sessions", lines)
        self.assertIn("  :help status", lines)

    def test_clear_help_explains_screen_only_behavior(self):
        lines = _help_lines("clear")
        self.assertIn("Use :clear to clear the visible terminal screen.", lines)

    def test_delete_help_explains_supported_targets(self):
        lines = _help_lines("delete")
        self.assertIn("Supported targets are var, function, and session.", lines)
        self.assertIn("  :delete session demo", lines)

    def test_functions_help_explains_definition_syntax(self):
        lines = _help_lines("functions")
        self.assertIn(
            "Define user functions with the form name(param1, param2) = expression.",
            lines,
        )
        self.assertIn("  :functions", lines)

    def test_reset_help_explains_in_memory_reset(self):
        lines = _help_lines("reset")
        self.assertIn("Use :reset to clear the current in-memory session.", lines)
        self.assertIn("Saved session files are not deleted.", lines)
        self.assertIn("use :reset --force or save first.", " ".join(lines).lower())

    def test_new_help_mentions_force_for_unsaved_changes(self):
        lines = _help_lines("new")
        self.assertIn("Use :new to start a fresh empty session.", lines)
        self.assertIn("use :new --force or save first.", " ".join(lines).lower())

    def test_status_help_mentions_dirty_state(self):
        lines = _help_lines("status")
        self.assertIn("The status includes the active session name, last save time, dirty state, and object counts.", lines)

    def test_vars_help_explains_assignment_syntax(self):
        lines = _help_lines("vars")
        self.assertIn("Assign user variables with the form name = expression.", lines)
        self.assertIn("  :vars", lines)

    def test_unknown_help_topic_lists_available_topics(self):
        lines = _help_lines("unknown")
        self.assertEqual(lines[0], "Unknown help topic 'unknown'.")
        self.assertEqual(
            lines[1],
            "Available topics: basics, clear, delete, functions, history, new, reset, sessions, status, vars",
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
        lines = _status_lines(context, SessionState())
        self.assertEqual(lines[0], "Session: <unsaved>")
        self.assertEqual(lines[1], "Saved at: never")
        self.assertEqual(lines[2], "Modified: no")

    def test_status_lines_for_saved_dirty_session(self):
        context = EvaluationContext()
        context.set_variable("radius", 5.0)
        context.set_function("area", ["r"], None)
        state = SessionState("demo", "2026-07-20T13:00:00+02:00", True)
        lines = _status_lines(context, state)
        self.assertEqual(lines[0], "Session: demo")
        self.assertEqual(lines[1], "Saved at: 2026-07-20T13:00:00+02:00")
        self.assertEqual(lines[2], "Modified: yes")
        self.assertEqual(lines[3], "User variables: 1")
        self.assertEqual(lines[4], "User functions: 1")

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
