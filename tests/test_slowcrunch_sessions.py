import re
import tempfile
import unittest
from pathlib import Path

from slowcrunch.core.errors import SessionError
from slowcrunch.engine import evaluate_expression
from slowcrunch.runtime.session_store import SessionStore


def _session_store(tempdir):
    temp_path = Path(tempdir)
    return SessionStore(temp_path / ".slowcrunch-sessions", mirror_root=temp_path)


class SlowCrunchSessionStoreTest(unittest.TestCase):
    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            context = None

            for expression in (
                "radius = 5",
                "area(r) = pi * r ^ 2",
                "area(radius)",
            ):
                _, context = evaluate_expression(expression, context)

            session = store.save(context, "demo", mirror_enabled=True)
            loaded_context, loaded_session = store.load("demo")
            result, loaded_context = evaluate_expression("area(radius)", loaded_context)

            self.assertEqual(session.name, "demo")
            self.assertEqual(loaded_session.name, "demo")
            self.assertEqual(session.mirror_path, Path(tempdir) / "demo.json")
            self.assertTrue((Path(tempdir) / "demo.json").exists())
            self.assertEqual(loaded_context.get_variable("radius"), 5.0)
            self.assertEqual(result, 78.53981633974483)
            self.assertEqual(
                loaded_context.user_functions()["area"].signature(),
                "area(r)",
            )
            self.assertEqual(loaded_context.entries[0]["expression"], "radius = 5")

    def test_save_generates_timestamp_name(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            _, context = evaluate_expression("2 + 2")
            session = store.save(context)
            self.assertRegex(session.name, r"^slowcrunch-\d{8}-\d{6}$")
            self.assertIsNone(session.mirror_path)
            self.assertFalse((Path(tempdir) / f"{session.name}.json").exists())

    def test_generated_session_names_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            _, context = evaluate_expression("2 + 2")
            first = store.save(context)
            second = store.save(context)

            self.assertNotEqual(first.name, second.name)
            self.assertEqual(len(store.list_sessions()), 2)

    def test_save_and_load_complex_values(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            context = None

            for expression in (
                "z = 2 + 3i",
                "sqrt(-1)",
                "z * i",
            ):
                _, context = evaluate_expression(expression, context)

            store.save(context, "complex", mirror_enabled=True)
            loaded_context, _ = store.load("complex")
            self.assertEqual(loaded_context.get_variable("z"), complex(2.0, 3.0))
            self.assertEqual(loaded_context.get_variable("ans"), complex(-3.0, 2.0))
            self.assertEqual(loaded_context.history, [complex(2.0, 3.0), 1j, complex(-3.0, 2.0)])
            self.assertEqual(loaded_context.entries[0]["result"], complex(2.0, 3.0))
            result, loaded_context = evaluate_expression("z + ans", loaded_context)

            self.assertEqual(result, complex(-1.0, 5.0))
            self.assertEqual(loaded_context.get_variable("ans"), complex(-1.0, 5.0))

    def test_save_and_load_list_values(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            context = None

            for expression in (
                "values = [1, 2, 4, 5]",
                "values",
            ):
                _, context = evaluate_expression(expression, context)

            store.save(context, "lists", mirror_enabled=True)
            loaded_context, _ = store.load("lists")

            self.assertEqual(loaded_context.get_variable("values"), [1.0, 2.0, 4.0, 5.0])
            self.assertEqual(loaded_context.entries[-1]["result"], [1.0, 2.0, 4.0, 5.0])

    def test_save_and_load_value_kinds(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            context = None

            for expression in (
                "bearing = 45deg",
                "work = 1h 20m 30s",
                "12h 20m 12s - 6h 49m 39s",
            ):
                _, context = evaluate_expression(expression, context)

            store.save(context, "kinds", mirror_enabled=True)
            loaded_context, _ = store.load("kinds")

            self.assertEqual(loaded_context.get_variable_kind("bearing"), "angle")
            self.assertEqual(loaded_context.get_variable_kind("work"), "duration")
            self.assertEqual(loaded_context.get_variable_kind("ans"), "duration")
            self.assertEqual(loaded_context.entries[-1]["kind"], "duration")

    def test_save_and_load_zero_tolerance(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            _, context = evaluate_expression("sin(360deg)")
            context.set_zero_tolerance(1e-12)

            store.save(context, "tolerance", mirror_enabled=True)
            loaded_context, _ = store.load("tolerance")

            self.assertEqual(loaded_context.zero_tolerance, 1e-12)

    def test_list_sessions_returns_saved_sessions(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            _, context = evaluate_expression("2 + 2")
            store.save(context, "alpha", mirror_enabled=True)
            store.save(context, "beta", mirror_enabled=True)
            sessions = store.list_sessions()
            self.assertEqual({session.name for session in sessions}, {"alpha", "beta"})

    def test_load_unknown_session_raises_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            with self.assertRaises(SessionError) as context:
                store.load("missing")
            self.assertEqual(str(context.exception), "Unknown session: missing")

    def test_delete_saved_session_removes_it(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            _, context = evaluate_expression("2 + 2")
            store.save(context, "demo", mirror_enabled=True)
            store.delete("demo")
            self.assertEqual(store.session_names(), [])

    def test_rename_saved_session_updates_name(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            _, context = evaluate_expression("2 + 2")
            store.save(context, "demo", mirror_enabled=True)
            session = store.rename("demo", "renamed")
            self.assertEqual(session.name, "renamed")
            self.assertEqual(store.session_names(), ["renamed"])
            loaded_context, loaded_session = store.load("renamed")
            self.assertEqual(loaded_session.name, "renamed")
            self.assertEqual(loaded_context.entries[0]["expression"], "2 + 2")
            self.assertTrue((Path(tempdir) / "demo.json").exists())
            self.assertTrue((Path(tempdir) / "renamed.json").exists())

    def test_rename_unknown_session_raises_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            with self.assertRaises(SessionError) as context:
                store.rename("missing", "renamed")
            self.assertEqual(str(context.exception), "Unknown session: missing")

    def test_rename_to_existing_session_raises_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            _, context = evaluate_expression("2 + 2")
            store.save(context, "alpha", mirror_enabled=True)
            store.save(context, "beta", mirror_enabled=True)
            with self.assertRaises(SessionError) as error:
                store.rename("alpha", "beta")
            self.assertEqual(str(error.exception), "Session already exists: beta")

    def test_delete_unknown_session_raises_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            with self.assertRaises(SessionError) as context:
                store.delete("missing")
            self.assertEqual(str(context.exception), "Unknown session: missing")

    def test_invalid_session_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            _, context = evaluate_expression("2 + 2")
            with self.assertRaises(SessionError) as error:
                store.save(context, "!!!")
            self.assertEqual(
                str(error.exception),
                "Session name must contain letters, numbers, underscores, or hyphens.",
            )

    def test_named_save_conflict_preserves_canonical_session(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = _session_store(tempdir)
            _, context = evaluate_expression("2 + 2")
            (Path(tempdir) / "demo.json").write_text("occupied", encoding="utf-8")

            with self.assertRaises(SessionError) as error:
                store.save(context, "demo", mirror_enabled=True)

            self.assertEqual(
                str(error.exception),
                "Current directory session file already exists: demo.json",
            )
            loaded_context, loaded_session = store.load("demo")
            self.assertEqual(loaded_session.name, "demo")
            self.assertEqual(loaded_context.entries[0]["expression"], "2 + 2")


if __name__ == "__main__":
    unittest.main()
