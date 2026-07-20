import re
import tempfile
import unittest

from slowcrunch.core.errors import SessionError
from slowcrunch.engine import evaluate_expression
from slowcrunch.runtime.session_store import SessionStore


class SlowCrunchSessionStoreTest(unittest.TestCase):
    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            context = None

            for expression in (
                "radius = 5",
                "area(r) = pi * r ^ 2",
                "area(radius)",
            ):
                _, context = evaluate_expression(expression, context)

            session = store.save(context, "demo")
            loaded_context, loaded_session = store.load("demo")
            result, loaded_context = evaluate_expression("area(radius)", loaded_context)

            self.assertEqual(session.name, "demo")
            self.assertEqual(loaded_session.name, "demo")
            self.assertEqual(loaded_context.get_variable("radius"), 5.0)
            self.assertEqual(result, 78.53981633974483)
            self.assertEqual(
                loaded_context.user_functions()["area"].signature(),
                "area(r)",
            )
            self.assertEqual(loaded_context.entries[0]["expression"], "radius = 5")

    def test_save_generates_timestamp_name(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            _, context = evaluate_expression("2 + 2")
            session = store.save(context)
            self.assertRegex(session.name, r"^session-\d{8}-\d{6}$")

    def test_save_and_load_complex_values(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            context = None

            for expression in (
                "z = 2 + 3i",
                "sqrt(-1)",
                "z * i",
            ):
                _, context = evaluate_expression(expression, context)

            store.save(context, "complex")
            loaded_context, _ = store.load("complex")
            self.assertEqual(loaded_context.get_variable("z"), complex(2.0, 3.0))
            self.assertEqual(loaded_context.get_variable("ans"), complex(-3.0, 2.0))
            self.assertEqual(loaded_context.history, [complex(2.0, 3.0), 1j, complex(-3.0, 2.0)])
            self.assertEqual(loaded_context.entries[0]["result"], complex(2.0, 3.0))
            result, loaded_context = evaluate_expression("z + ans", loaded_context)

            self.assertEqual(result, complex(-1.0, 5.0))
            self.assertEqual(loaded_context.get_variable("ans"), complex(-1.0, 5.0))

    def test_list_sessions_returns_saved_sessions(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            _, context = evaluate_expression("2 + 2")
            store.save(context, "alpha")
            store.save(context, "beta")
            sessions = store.list_sessions()
            self.assertEqual({session.name for session in sessions}, {"alpha", "beta"})

    def test_load_unknown_session_raises_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            with self.assertRaises(SessionError) as context:
                store.load("missing")
            self.assertEqual(str(context.exception), "Unknown session: missing")

    def test_delete_saved_session_removes_it(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            _, context = evaluate_expression("2 + 2")
            store.save(context, "demo")
            store.delete("demo")
            self.assertEqual(store.session_names(), [])

    def test_rename_saved_session_updates_name(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            _, context = evaluate_expression("2 + 2")
            store.save(context, "demo")
            session = store.rename("demo", "renamed")
            self.assertEqual(session.name, "renamed")
            self.assertEqual(store.session_names(), ["renamed"])
            loaded_context, loaded_session = store.load("renamed")
            self.assertEqual(loaded_session.name, "renamed")
            self.assertEqual(loaded_context.entries[0]["expression"], "2 + 2")

    def test_rename_unknown_session_raises_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            with self.assertRaises(SessionError) as context:
                store.rename("missing", "renamed")
            self.assertEqual(str(context.exception), "Unknown session: missing")

    def test_rename_to_existing_session_raises_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            _, context = evaluate_expression("2 + 2")
            store.save(context, "alpha")
            store.save(context, "beta")
            with self.assertRaises(SessionError) as error:
                store.rename("alpha", "beta")
            self.assertEqual(str(error.exception), "Session already exists: beta")

    def test_delete_unknown_session_raises_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            with self.assertRaises(SessionError) as context:
                store.delete("missing")
            self.assertEqual(str(context.exception), "Unknown session: missing")

    def test_invalid_session_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SessionStore(tempdir)
            _, context = evaluate_expression("2 + 2")
            with self.assertRaises(SessionError) as error:
                store.save(context, "!!!")
            self.assertEqual(
                str(error.exception),
                "Session name must contain letters, numbers, underscores, or hyphens.",
            )


if __name__ == "__main__":
    unittest.main()
