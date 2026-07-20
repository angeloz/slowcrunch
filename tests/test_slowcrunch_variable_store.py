import json
import tempfile
import unittest
from pathlib import Path

from slowcrunch.core.errors import SessionError
from slowcrunch.engine import evaluate_expression
from slowcrunch.runtime.variable_store import VariableStore


class SlowCrunchVariableStoreTest(unittest.TestCase):
    def test_save_and_load_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = VariableStore()
            context = None

            for expression in (
                "radius = 5",
                "values = [1, 2, 4, 5]",
                "bearing = 45deg",
            ):
                _, context = evaluate_expression(expression, context)

            info = store.save(context, Path(tempdir) / "vars.json")
            variables, variable_kinds, loaded_info = store.load(Path(tempdir) / "vars.json")

            self.assertEqual(info.format_name, "json")
            self.assertEqual(info.variable_count, 3)
            self.assertEqual(loaded_info.variable_count, 3)
            self.assertEqual(variables["radius"], 5.0)
            self.assertEqual(variables["values"], [1.0, 2.0, 4.0, 5.0])
            self.assertEqual(variable_kinds["bearing"], "angle")

    def test_load_plain_json_mapping(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = VariableStore()
            path = Path(tempdir) / "plain.json"
            path.write_text(
                json.dumps(
                    {
                        "radius": 5,
                        "values": [1, 2, 4, 5],
                    }
                ),
                encoding="utf-8",
            )

            variables, variable_kinds, info = store.load(path)

            self.assertEqual(info.format_name, "json")
            self.assertEqual(variables["radius"], 5.0)
            self.assertEqual(variables["values"], [1.0, 2.0, 4.0, 5.0])
            self.assertEqual(variable_kinds, {})

    def test_save_and_load_csv_roundtrip(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = VariableStore()
            context = None

            for expression in (
                "radius = 5",
                "values = [1, 2, 4, 5]",
                "work = 1h 20m 30s",
            ):
                _, context = evaluate_expression(expression, context)

            info = store.save(context, Path(tempdir) / "vars.csv")
            variables, variable_kinds, loaded_info = store.load(Path(tempdir) / "vars.csv")

            self.assertEqual(info.format_name, "csv")
            self.assertEqual(loaded_info.variable_count, 3)
            self.assertEqual(variables["radius"], 5.0)
            self.assertEqual(variables["values"], [1.0, 2.0, 4.0, 5.0])
            self.assertEqual(variable_kinds["work"], "duration")

    def test_invalid_json_variable_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = VariableStore()
            path = Path(tempdir) / "invalid.json"
            path.write_text(json.dumps({"bad-name": 5}), encoding="utf-8")

            with self.assertRaises(SessionError) as error:
                store.load(path)

            self.assertEqual(str(error.exception), "Invalid variable name in variable file: bad-name")

    def test_invalid_csv_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = VariableStore()
            path = Path(tempdir) / "invalid.csv"
            path.write_text("name,kind,value\nvalues,,not-json\n", encoding="utf-8")

            with self.assertRaises(SessionError) as error:
                store.load(path)

            self.assertEqual(
                str(error.exception),
                "Variable CSV row 2 has an invalid JSON value for 'values'.",
            )

    def test_unsupported_variable_file_format_is_rejected(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = VariableStore()
            path = Path(tempdir) / "vars.txt"

            with self.assertRaises(SessionError) as error:
                store.load(path)

            self.assertEqual(str(error.exception), "Variable file format must be json or csv.")
