import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from slowcrunch.core.errors import SessionError
from slowcrunch.runtime.ast_codec import decode_node, encode_node
from slowcrunch.runtime.context import EvaluationContext

DEFAULT_SESSION_DIR = ".slowcrunch-sessions"
SESSION_ENV_VAR = "SLOWCRUNCH_SESSION_DIR"
SESSION_FILE_SUFFIX = ".json"
SESSION_VERSION = 1


@dataclass(frozen=True)
class SessionInfo:
    name: str
    saved_at: str
    path: Path


class SessionStore:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else self.default_root()

    @staticmethod
    def default_root():
        configured = os.environ.get(SESSION_ENV_VAR)
        if configured:
            return Path(configured)
        return Path.cwd() / DEFAULT_SESSION_DIR

    def save(self, context, name=None):
        self.root.mkdir(parents=True, exist_ok=True)
        session_name = self._normalize_name(name) if name else self._generated_name()
        saved_at = datetime.now().astimezone().isoformat(timespec="seconds")
        path = self._path_for(session_name)
        payload = self._serialize_context(context, session_name, saved_at)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return SessionInfo(session_name, saved_at, path)

    def load(self, name):
        session_name = self._normalize_name(name)
        path = self._path_for(session_name)
        if not path.exists():
            raise SessionError(f"Unknown session: {session_name}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SessionError(f"Session file is not valid JSON: {path.name}") from error

        if data.get("version") != SESSION_VERSION:
            raise SessionError(f"Unsupported session version: {data.get('version')}")

        return self._deserialize_context(data), SessionInfo(
            data["name"],
            data["saved_at"],
            path,
        )

    def list_sessions(self):
        if not self.root.exists():
            return []

        sessions = []
        for path in sorted(self.root.glob(f"*{SESSION_FILE_SUFFIX}")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if "name" not in data or "saved_at" not in data:
                continue
            sessions.append(SessionInfo(data["name"], data["saved_at"], path))

        return sorted(sessions, key=lambda session: session.saved_at, reverse=True)

    def session_names(self):
        return [session.name for session in self.list_sessions()]

    def delete(self, name):
        session_name = self._normalize_name(name)
        path = self._path_for(session_name)
        if not path.exists():
            raise SessionError(f"Unknown session: {session_name}")
        path.unlink()

    def rename(self, old_name, new_name):
        old_session_name = self._normalize_name(old_name)
        new_session_name = self._normalize_name(new_name)
        old_path = self._path_for(old_session_name)
        new_path = self._path_for(new_session_name)

        if not old_path.exists():
            raise SessionError(f"Unknown session: {old_session_name}")
        if new_path.exists():
            raise SessionError(f"Session already exists: {new_session_name}")

        try:
            data = json.loads(old_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SessionError(f"Session file is not valid JSON: {old_path.name}") from error

        data["name"] = new_session_name
        new_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        old_path.unlink()
        return SessionInfo(new_session_name, data["saved_at"], new_path)

    def _serialize_context(self, context, name, saved_at):
        return {
            "version": SESSION_VERSION,
            "name": name,
            "saved_at": saved_at,
            "ans": context.variables["ans"],
            "history": context.history,
            "entries": context.entries,
            "variables": context.user_variables(),
            "functions": [
                {
                    "name": function.name,
                    "parameters": list(function.parameters),
                    "body": encode_node(function.body),
                }
                for function in context.user_functions().values()
            ],
        }

    def _deserialize_context(self, data):
        context = EvaluationContext()

        for name, value in data.get("variables", {}).items():
            context.set_variable(name, value)

        for function in data.get("functions", []):
            context.set_function(
                function["name"],
                function["parameters"],
                decode_node(function["body"]),
            )

        context.history = list(data.get("history", []))
        context.entries = list(data.get("entries", []))
        context.variables["ans"] = data.get("ans", 0.0)
        return context

    def _path_for(self, name):
        return self.root / f"{name}{SESSION_FILE_SUFFIX}"

    def _normalize_name(self, name):
        normalized = re.sub(r"[^A-Za-z0-9_-]+", "-", name.strip()).strip("-_")
        if not normalized:
            raise SessionError("Session name must contain letters, numbers, underscores, or hyphens.")
        return normalized

    def _generated_name(self):
        return datetime.now().astimezone().strftime("session-%Y%m%d-%H%M%S")
