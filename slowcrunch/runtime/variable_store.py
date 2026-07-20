import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

from slowcrunch.core.errors import SessionError
from slowcrunch.runtime.value_codec import decode_value, encode_value

SUPPORTED_VARIABLE_FORMATS = ("csv", "json")
VARIABLE_FILE_TYPE = "slowcrunch-variables"
VARIABLE_FILE_VERSION = 1
VARIABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class VariableFileInfo:
    path: Path
    format_name: str
    variable_count: int


class VariableStore:
    def save(self, context, path, format_name=None):
        file_path = Path(path)
        resolved_format = self._resolve_format(file_path, format_name)
        payload = self._serialize_context(context)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if resolved_format == "json":
            self._write_json(file_path, payload)
        else:
            self._write_csv(file_path, payload)

        return VariableFileInfo(file_path, resolved_format, len(payload["variables"]))

    def load(self, path, format_name=None):
        file_path = Path(path)
        resolved_format = self._resolve_format(file_path, format_name)
        if not file_path.exists():
            raise SessionError(f"Variable file not found: {file_path}")

        if resolved_format == "json":
            variables, variable_kinds = self._read_json(file_path)
        else:
            variables, variable_kinds = self._read_csv(file_path)

        return variables, variable_kinds, VariableFileInfo(
            file_path,
            resolved_format,
            len(variables),
        )

    def _resolve_format(self, path, format_name):
        candidate = format_name.lower() if format_name is not None else path.suffix.lower().lstrip(".")
        if candidate not in SUPPORTED_VARIABLE_FORMATS:
            raise SessionError("Variable file format must be json or csv.")
        return candidate

    def _serialize_context(self, context):
        return {
            "type": VARIABLE_FILE_TYPE,
            "version": VARIABLE_FILE_VERSION,
            "variables": encode_value(context.user_variables()),
            "variable_kinds": context.user_variable_kinds(),
        }

    def _write_json(self, path, payload):
        try:
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        except OSError as error:
            raise SessionError(f"Could not write variable file: {path}") from error

    def _read_json(self, path):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise SessionError(f"Could not read variable file: {path}") from error
        except json.JSONDecodeError as error:
            raise SessionError(f"Variable file is not valid JSON: {path}") from error

        if not isinstance(data, dict):
            raise SessionError("Variable JSON file must contain an object.")

        if data.get("type") == VARIABLE_FILE_TYPE:
            if data.get("version") != VARIABLE_FILE_VERSION:
                raise SessionError(f"Unsupported variable file version: {data.get('version')}")
            raw_variables = data.get("variables", {})
            raw_variable_kinds = data.get("variable_kinds", {})
        else:
            raw_variables = data
            raw_variable_kinds = {}

        if not isinstance(raw_variables, dict):
            raise SessionError("Variable JSON file must contain an object of variables.")
        if not isinstance(raw_variable_kinds, dict):
            raise SessionError("Variable JSON file must contain an object of variable kinds.")

        self._validate_variable_names(raw_variables.keys())
        self._validate_variable_kind_names(raw_variables, raw_variable_kinds)

        variables = {
            name: decode_value(value)
            for name, value in raw_variables.items()
        }
        variable_kinds = {
            name: kind
            for name, kind in raw_variable_kinds.items()
            if kind is not None
        }
        return variables, variable_kinds

    def _write_csv(self, path, payload):
        try:
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=("name", "kind", "value"))
                writer.writeheader()
                for name in sorted(payload["variables"]):
                    writer.writerow(
                        {
                            "name": name,
                            "kind": payload["variable_kinds"].get(name, ""),
                            "value": json.dumps(payload["variables"][name], separators=(",", ":")),
                        }
                    )
        except OSError as error:
            raise SessionError(f"Could not write variable file: {path}") from error

    def _read_csv(self, path):
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = reader.fieldnames or []
                if "name" not in fieldnames or "value" not in fieldnames:
                    raise SessionError("Variable CSV file must contain name and value columns.")

                variables = {}
                variable_kinds = {}
                for row_number, row in enumerate(reader, start=2):
                    name = (row.get("name") or "").strip()
                    if not name:
                        raise SessionError(f"Variable CSV row {row_number} is missing a name.")
                    if name in variables:
                        raise SessionError(f"Duplicate variable in CSV file: {name}")

                    self._validate_variable_names((name,))

                    raw_value = row.get("value")
                    if raw_value is None:
                        raise SessionError(f"Variable CSV row {row_number} is missing a value.")
                    try:
                        encoded_value = json.loads(raw_value)
                    except json.JSONDecodeError as error:
                        raise SessionError(
                            f"Variable CSV row {row_number} has an invalid JSON value for '{name}'."
                        ) from error

                    variables[name] = decode_value(encoded_value)
                    kind = (row.get("kind") or "").strip()
                    if kind:
                        variable_kinds[name] = kind
        except OSError as error:
            raise SessionError(f"Could not read variable file: {path}") from error
        except csv.Error as error:
            raise SessionError(f"Variable CSV file is invalid: {path}") from error

        return variables, variable_kinds

    def _validate_variable_names(self, names):
        for name in names:
            if not isinstance(name, str) or not VARIABLE_NAME_PATTERN.match(name):
                raise SessionError(f"Invalid variable name in variable file: {name}")

    def _validate_variable_kind_names(self, variables, variable_kinds):
        for name in variable_kinds:
            if name not in variables:
                raise SessionError(f"Variable kind refers to an unknown variable: {name}")
