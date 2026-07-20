import shlex
from dataclasses import dataclass

try:
    import readline
except ImportError:  # pragma: no cover
    readline = None

from slowcrunch.core.errors import IncompleteInputError, SessionError, SlowCrunchError
from slowcrunch.engine import evaluate_expression, parse_input
from slowcrunch.runtime.builtins import builtin_function_groups
from slowcrunch.runtime.context import EvaluationContext
from slowcrunch.runtime.numbers import ANGLE_FORMAT_MODES, FORMAT_MODES, format_value
from slowcrunch.runtime.session_store import SessionStore

REPL_COMMANDS = (
    ":angles",
    ":clear",
    ":delete",
    ":format",
    ":functions",
    ":help",
    ":history",
    ":load",
    ":new",
    ":rename-session",
    ":reset",
    ":save",
    ":saveas",
    ":sessions",
    ":status",
    ":tolerance",
    ":vars",
)
REPL_KEYWORDS = ("exit", "quit")
HELP_TOPICS = ("angles", "basics", "clear", "delete", "format", "functions", "history", "new", "reset", "sessions", "status", "tolerance", "vars")
DELETE_TARGETS = ("function", "session", "var")


@dataclass
class SessionState:
    current_name: str | None = None
    last_saved_at: str | None = None
    dirty: bool = False


@dataclass
class DisplaySettings:
    format_mode: str = "plain"
    angle_mode: str = "deg"


def _completion_candidates(context, text, line_buffer="", begidx=0, session_names=None):
    stripped_buffer = line_buffer.lstrip()

    if stripped_buffer.startswith(":help ") and not text.startswith(":"):
        pool = HELP_TOPICS
    elif stripped_buffer.startswith(":angles ") and not text.startswith(":"):
        pool = ANGLE_FORMAT_MODES
    elif stripped_buffer.startswith(":format ") and not text.startswith(":"):
        pool = FORMAT_MODES
    elif stripped_buffer.startswith(":delete ") and not text.startswith(":"):
        pool = _delete_completion_pool(context, stripped_buffer, session_names)
    elif stripped_buffer.startswith(":load ") and not text.startswith(":"):
        pool = session_names or ()
    elif line_buffer.startswith(":") or text.startswith(":") or (begidx == 0 and text.startswith(":")):
        pool = REPL_COMMANDS
    else:
        function_candidates = [f"{name}(" for name in context.function_names()]
        variable_candidates = context.variable_names()
        pool = tuple(sorted(set(function_candidates + variable_candidates + list(REPL_KEYWORDS))))

    return [candidate for candidate in pool if candidate.startswith(text)]


def _delete_completion_pool(context, line_buffer, session_names):
    remainder = line_buffer[len(":delete "):].strip()
    if not remainder or " " not in remainder:
        return DELETE_TARGETS

    target = remainder.split()[0]
    if target == "var":
        return tuple(sorted(context.user_variables()))
    if target == "function":
        return tuple(sorted(context.user_functions()))
    if target == "session":
        return tuple(session_names or ())
    return ()


def _make_completer(context, session_store):
    def completer(text, state):
        line_buffer = readline.get_line_buffer() if readline is not None else ""
        begidx = readline.get_begidx() if readline is not None else 0
        matches = _completion_candidates(
            context,
            text,
            line_buffer,
            begidx,
            session_store.session_names(),
        )
        if state < len(matches):
            return matches[state]
        return None

    return completer


def _configure_readline(context, session_store):
    if readline is None:
        return
    readline.set_completer_delims(" \t\n+-*/^()=,")
    readline.set_completer(_make_completer(context, session_store))
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind('"\\e[A": previous-history')
    readline.parse_and_bind('"\\e[B": next-history')


def _print_history(context, display_settings, query=None):
    for line in _history_lines(context, display_settings, query):
        print(line)


def _render_value(value, display_settings, kind=None, zero_tolerance=None):
    return format_value(
        value,
        display_settings.format_mode,
        kind,
        display_settings.angle_mode,
        zero_tolerance if zero_tolerance is not None else 0.0,
    )


def _print_variables(context, display_settings):
    variables = context.user_variables()
    if not variables:
        print("No user variables.")
        return
    for name in sorted(variables):
        print(
            f"{name} = {_render_value(variables[name], display_settings, context.get_variable_kind(name), context.zero_tolerance)}"
        )


def _print_functions(context):
    functions = context.user_functions()
    if not functions:
        print("No user-defined functions.")
        return
    for name in sorted(functions):
        print(functions[name].signature())


def _print_sessions(session_store):
    sessions = session_store.list_sessions()
    if not sessions:
        print("No saved sessions.")
        return
    for session in sessions:
        print(f"{session.name}  {session.saved_at}")


def _status_lines(context, session_state, display_settings):
    session_name = session_state.current_name or "<unsaved>"
    saved_at = session_state.last_saved_at or "never"
    modified = "yes" if session_state.dirty else "no"
    return [
        f"Session: {session_name}",
        f"Saved at: {saved_at}",
        f"Modified: {modified}",
        f"Format: {display_settings.format_mode}",
        f"Angles: {display_settings.angle_mode}",
        f"Zero tolerance: {context.zero_tolerance:.12g}",
        f"User variables: {len(context.user_variables())}",
        f"User functions: {len(context.user_functions())}",
        f"History entries: {len(context.entries)}",
        f"Numeric results: {len(context.history)}",
    ]


def _print_status(context, session_state, display_settings):
    for line in _status_lines(context, session_state, display_settings):
        print(line)


def _history_lines(context, display_settings, query=None):
    if not context.entries:
        return ["No history yet."]

    entries = list(enumerate(context.entries, start=1))
    if query:
        lowered_query = query.lower()
        entries = [
            (index, entry)
            for index, entry in entries
            if lowered_query in entry["expression"].lower()
            or lowered_query in _render_value(
                entry["result"],
                display_settings,
                entry.get("kind"),
                context.zero_tolerance,
            ).lower()
        ]
        if not entries:
            return [f"No history entries matching '{query}'."]

    return [
        f"{index}: {entry['expression']} = {_render_value(entry['result'], display_settings, entry.get('kind'), context.zero_tolerance)}"
        for index, entry in entries
    ]


def _history_replay_entry(context, token):
    if not token.startswith("!"):
        raise SessionError("History replay requires !index, such as :history !3.")

    raw_index = token[1:]
    if not raw_index.isdigit() or int(raw_index) < 1:
        raise SessionError("History replay requires !index, such as :history !3.")

    entry_index = int(raw_index)
    if entry_index > len(context.entries):
        raise SessionError(f"Unknown history entry: {entry_index}")

    return entry_index, context.entries[entry_index - 1]


def _help_lines(topic=None):
    if topic is None:
        return [
            "Available commands:",
            ":angles [MODE] Show or change the angle output mode.",
            ":clear    Clear the screen.",
            ":delete   Delete a variable, function, or saved session.",
            ":format [MODE] Show or change the numeric output mode.",
            ":functions Show user-defined functions.",
            ":help [topic] Show general help or help for a topic.",
            ":history [text|!index] Show, filter, or replay history.",
            ":load NAME Load a saved session.",
            ":new      Start a new empty session.",
            ":rename-session NAME Rename the current saved session.",
            ":reset    Reset the current in-memory session.",
            ":save [NAME] Save the current session.",
            ":saveas NAME Save the current session under a new name.",
            ":sessions List saved sessions.",
            ":status   Show the current session state.",
            ":tolerance [VALUE] Show or change the zero tolerance.",
            ":vars    Show user-defined variables.",
            "quit     Exit the application.",
            "exit     Exit the application.",
            "Help topics: angles, basics, clear, delete, format, functions, history, new, reset, sessions, status, tolerance, vars",
            "Examples:",
            "  :help angles",
            "  :help delete",
            "  :help format",
            "  :help functions",
            "  :help status",
            "  :help sessions",
            "  :help tolerance",
            "  :help vars",
            "  2 + 3 * 4",
            "  radius = 5",
            "  10k",
            "  area(r) = pi * r ^ 2",
        ]

    if topic == "angles":
        return [
            "Help: angles",
            "Use :angles to inspect or change the angle output mode.",
            "Available modes: deg, dms, rad.",
            "deg renders angle results in decimal degrees, such as 45deg.",
            "dms renders angle results as degrees, minutes, and seconds.",
            "rad renders angle results in radians with a rad suffix.",
            "This affects angle-typed results such as 90deg / 2 or arg(i).",
            "Use compact pi-multiples such as 2pi or 0.5pi for angle-typed radian input.",
            "Use 360deg or 2 * 180deg when you want 2*pi as an angle-typed value.",
            "Use 2 * pi when you only need the numeric radian value.",
            "Examples:",
            "  :angles",
            "  :angles deg",
            "  :angles dms",
            "  :angles rad",
            "  2pi",
            "  360deg",
            "  360deg / 2",
            "  arg(i)",
        ]

    if topic == "basics":
        return [
            "Help: basics",
            "Enter expressions directly at the prompt.",
            "Supported operators: +, -, *, /, ^",
            "Numbers can use scientific notation such as 1.2e6.",
            "Numbers can use SI prefixes such as 10k, 1M, 220u, or 3f.",
            "Lists can use bracket literals such as [1, 2, 3] and can be assigned to variables.",
            "Angles can use explicit units such as 90deg, 1.5rad, or 2mrad.",
            "Angle arithmetic keeps angle-style output when the result stays an angle.",
            "Use :angles to choose whether angle results are shown as deg, dms, or rad.",
            "Use compact pi-multiples such as 2pi or 0.5pi for angle-typed radian input.",
            "Use 360deg or 2 * 180deg when you want 2*pi to keep angle-style output.",
            "Durations can use explicit units such as 1h 20m 30s, 45min, or 90s.",
            "Use min for standalone minutes; the short m form is accepted inside composite durations.",
            "Duration arithmetic keeps duration-style output when the result stays a duration.",
            "Use :tolerance to control when very small values are normalized to zero.",
            "Use deg(x), dms(x), and hms(x) to format angles and durations explicitly.",
            "Use parentheses to group sub-expressions.",
            "Use a trailing ';' to continue a multi-statement program on the next line.",
            "The continuation prompt is '.. ' while additional input is expected.",
            "Built-in constants include pi, e, and i.",
            "The ans variable stores the last numeric result.",
            "Examples:",
            "  2 + 3 * 4",
            "  2 + 3i",
            "  10k + 25",
            "  values = [1, 2, 3]",
            "  sin(90deg)",
            "  2pi",
            "  360deg",
            "  90deg / 2",
            "  1h 20m 30s",
            "  12h 20m 12s - 6h 49m 39s",
            "  deg(pi / 2)",
            "  dms(pi / 6)",
            "  hms(4830)",
            "  :tolerance 1e-12",
            "  1.2e6",
            "  radius = 5;",
            "  .. area(r) = pi * r ^ 2;",
            "  .. area(radius)",
            "  (1 + 2) * 3",
            "  sqrt(-1)",
        ]

    if topic == "format":
        return [
            "Help: format",
            "Use :format to inspect or change the numeric output mode.",
            "Available modes: plain, scientific, engineering, si.",
            "Use :angles for angle-specific output policy.",
            "Use :tolerance for near-zero normalization.",
            "Plain keeps the default Python-like decimal rendering.",
            "Scientific uses mantissa and exponent, such as 1.2e6.",
            "Engineering keeps exponents in steps of three, such as 12e3.",
            "SI uses engineering steps with SI prefixes, such as 12k or 220u.",
            "Examples:",
            "  :format",
            "  :format scientific",
            "  :format engineering",
            "  :format si",
        ]

    if topic == "functions":
        category_lines = [
            f"{category}: {', '.join(functions)}"
            for category, functions in builtin_function_groups()
        ]
        return [
            "Help: functions",
            "Supported built-in functions are grouped by category below.",
            "These functions also accept complex arguments.",
            "Statistics functions currently use list arguments such as [1, 2, 3].",
            "Inverse trigonometric functions and arg return angle-typed results and follow :angles.",
            *category_lines,
            "Define user functions with the form name(param1, param2) = expression.",
            "Function parameters are local to the function body.",
            "User-defined functions can reference global variables.",
            "Examples:",
            "  square(x) = x ^ 2",
            "  area(r) = pi * r ^ 2",
            "  asin(1)",
            "  atan2(1, 1)",
            "  cot(45deg)",
            "  sinh(1)",
            "  exp(2)",
            "  len([1, 2, 3])",
            "  sum([1, 2, 3])",
            "  mean([1, 2, 3])",
            "  sqrt(-1)",
            "  conj(2 + 3i)",
            "  arg(i)",
            "  deg(pi / 2)",
            "  dms(pi / 6)",
            "  hms(4830)",
            "  area(5)",
            "  :functions",
        ]

    if topic == "clear":
        return [
            "Help: clear",
            "Use :clear to clear the visible terminal screen.",
            "This command does not modify variables, functions, history, or saved sessions.",
            "Example:",
            "  :clear",
        ]

    if topic == "history":
        return [
            "Help: history",
            "Use :history to list evaluated inputs and their results.",
            "Use :history text to filter entries by expression or rendered result.",
            "Use :history !index to replay a previous entry.",
            "The history includes assignments and function definitions.",
            "Use ans to reuse the last numeric result.",
            "Examples:",
            "  10 / 2",
            "  ans + 3",
            "  :history",
            "  :history area",
            "  :history !3",
        ]

    if topic == "new":
        return [
            "Help: new",
            "Use :new to start a fresh empty session.",
            "If the current session has unsaved changes, use :new --force or save first.",
            "A new session starts unnamed and not modified.",
            "Example:",
            "  :new",
        ]

    if topic == "delete":
        return [
            "Help: delete",
            "Use :delete with an explicit target to remove state safely.",
            "Supported targets are var, function, and session.",
            "Examples:",
            "  :delete var radius",
            "  :delete function area",
            "  :delete session demo",
        ]

    if topic == "reset":
        return [
            "Help: reset",
            "Use :reset to clear the current in-memory session.",
            "This removes user variables, user-defined functions, ans history, and recorded entries.",
            "Saved session files are not deleted.",
            "If the current session has unsaved changes, use :reset --force or save first.",
            "Example:",
            "  :reset",
        ]

    if topic == "vars":
        return [
            "Help: vars",
            "Assign user variables with the form name = expression.",
            "Use :vars to list user-defined variables.",
            "Protected names such as ans, pi, e, and i cannot be reassigned.",
            "Examples:",
            "  radius = 5",
            "  z = 2 + 3i",
            "  current = 4.7m",
            "  mass = 12 / 3",
            "  pi * radius ^ 2",
            "  :vars",
        ]

    if topic == "sessions":
        return [
            "Help: sessions",
            "Use :save [name] to store the current session as JSON.",
            "Use :saveas name to save under a new explicit name.",
            "If no name is provided, slowcrunch generates one from the current date and time.",
            "Use :sessions to list available saved sessions.",
            "Use :status to inspect the current session state.",
            "Use :load name to replace the current session with a saved one.",
            "Use :rename-session name to rename the current saved session on disk.",
            "Session files are stored in .slowcrunch-sessions by default.",
            "Examples:",
            "  :status",
            "  :saveas demo",
            "  :save",
            "  :save demo",
            "  :sessions",
            "  :load demo",
        ]

    if topic == "status":
        return [
            "Help: status",
            "Use :status to inspect the current session.",
            "The status includes the active session name, last save time, dirty state, numeric format mode, angle mode, zero tolerance, and object counts.",
            "Examples:",
            "  :status",
            "  :save demo",
            "  :status",
        ]

    if topic == "tolerance":
        return [
            "Help: tolerance",
            "Use :tolerance to inspect or change the zero tolerance.",
            "Values with absolute magnitude below the tolerance are normalized to zero.",
            "This affects evaluation results, ans, history rendering, and near-zero angle outputs.",
            "Use a non-negative floating-point value, such as 1e-12.",
            "Examples:",
            "  :tolerance",
            "  :tolerance 1e-12",
            "  sin(360deg)",
        ]

    return [
        f"Unknown help topic '{topic}'.",
        "Available topics: angles, basics, clear, delete, format, functions, history, new, reset, sessions, status, tolerance, vars",
    ]


def _print_help(topic=None):
    for line in _help_lines(topic):
        print(line)


def _clear_screen():
    print("\033[2J\033[H", end="")


def _parse_command(line):
    try:
        return shlex.split(line)
    except ValueError as error:
        raise SessionError(f"Invalid command syntax: {error}") from error


def _requires_continuation(text):
    try:
        parse_input(text)
    except IncompleteInputError:
        return True
    except SlowCrunchError:
        return False
    return False


def _command_force_requested(arguments):
    return "--force" in arguments


def _command_arguments(arguments):
    return [argument for argument in arguments if argument != "--force"]


def _ensure_clean_session(session_state, action, force_requested):
    if session_state.dirty and not force_requested:
        raise SessionError(f"Current session has unsaved changes. Use {action} --force or :save first.")


def _mark_session_saved(session_state, session):
    session_state.current_name = session.name
    session_state.last_saved_at = session.saved_at
    session_state.dirty = False


def _mark_session_dirty(session_state):
    session_state.dirty = True


def _start_new_session():
    return EvaluationContext(), SessionState()


def _read_statement():
    lines = []

    while True:
        prompt = ">> " if not lines else ".. "

        try:
            line = input(prompt)
        except EOFError:
            print()
            return None
        except KeyboardInterrupt:
            if lines:
                print("\nCancelled multi-line input.")
                return ""
            raise

        if not lines and not line.strip():
            continue

        if lines and line.lstrip().startswith(":"):
            print("Error: commands are not available during multi-line input. Press Ctrl+C to cancel.")
            continue

        lines.append(line)
        text = "\n".join(lines)

        if _requires_continuation(text):
            continue

        return text


def run_repl(session_store=None):
    context = EvaluationContext()
    session_state = SessionState()
    display_settings = DisplaySettings()
    session_store = session_store or SessionStore()
    _configure_readline(context, session_store)

    print("slowcrunch")
    print("Type an expression or 'quit' to exit.")
    print(
        "Commands: :angles, :clear, :delete, :format, :functions, :help, :history, :load, "
        ":new, :rename-session, :reset, :save, :saveas, :sessions, :status, :tolerance, :vars"
    )

    while True:
        try:
            line = _read_statement()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nInterrupted.")
            break

        if line is None:
            break

        line = line.strip()
        if not line:
            continue

        if line.lower() in {"quit", "exit"}:
            break

        if line.startswith(":"):
            try:
                parts = _parse_command(line)
                command = parts[0]

                if command == ":help":
                    topic = parts[1] if len(parts) > 1 else None
                    _print_help(topic)
                    continue

                if command == ":functions":
                    _print_functions(context)
                    continue

                if command == ":angles":
                    if len(parts) > 2:
                        raise SessionError("Usage: :angles [deg|dms|rad]")
                    if len(parts) == 1:
                        print(f"Angle format: {display_settings.angle_mode}")
                        continue
                    mode = parts[1].lower()
                    if mode not in ANGLE_FORMAT_MODES:
                        raise SessionError("Usage: :angles [deg|dms|rad]")
                    display_settings.angle_mode = mode
                    print(f"Angle format set to {mode}.")
                    continue

                if command == ":format":
                    if len(parts) > 2:
                        raise SessionError("Usage: :format [plain|scientific|engineering|si]")
                    if len(parts) == 1:
                        print(f"Output format: {display_settings.format_mode}")
                        continue
                    mode = parts[1].lower()
                    if mode not in FORMAT_MODES:
                        raise SessionError("Usage: :format [plain|scientific|engineering|si]")
                    display_settings.format_mode = mode
                    print(f"Output format set to {mode}.")
                    continue

                if command == ":status":
                    if len(parts) != 1:
                        raise SessionError("Usage: :status")
                    _print_status(context, session_state, display_settings)
                    continue

                if command == ":tolerance":
                    if len(parts) > 2:
                        raise SessionError("Usage: :tolerance [value]")
                    if len(parts) == 1:
                        print(f"Zero tolerance: {context.zero_tolerance:.12g}")
                        continue
                    try:
                        context.set_zero_tolerance(float(parts[1]))
                    except ValueError as error:
                        raise SessionError("Usage: :tolerance [value]") from error
                    except SlowCrunchError as error:
                        raise SessionError(str(error)) from error
                    print(f"Zero tolerance set to {context.zero_tolerance:.12g}.")
                    continue

                if command == ":clear":
                    if len(parts) != 1:
                        raise SessionError("Usage: :clear")
                    _clear_screen()
                    continue

                if command == ":history":
                    if len(parts) == 1:
                        _print_history(context, display_settings)
                        continue

                    if parts[1].startswith("!"):
                        if len(parts) != 2:
                            raise SessionError("Usage: :history [text|!index]")
                        entry_index, entry = _history_replay_entry(context, parts[1])
                        preview = entry["expression"].replace("\n", "\\n")
                        print(f"Replaying #{entry_index}: {preview}")
                        try:
                            result, context = evaluate_expression(entry["expression"], context)
                        except SlowCrunchError as error:
                            print(f"Error: {error}")
                            continue
                        _mark_session_dirty(session_state)
                        print(_render_value(result, display_settings, context.entries[-1].get("kind"), context.zero_tolerance))
                        continue

                    _print_history(context, display_settings, " ".join(parts[1:]))
                    continue

                if command == ":vars":
                    _print_variables(context, display_settings)
                    continue

                if command == ":sessions":
                    _print_sessions(session_store)
                    continue

                if command == ":save":
                    if len(parts) > 2:
                        raise SessionError("Usage: :save [name]")
                    name = parts[1] if len(parts) == 2 else session_state.current_name
                    session = session_store.save(context, name)
                    _mark_session_saved(session_state, session)
                    print(f"Saved session '{session.name}' at {session.saved_at}")
                    continue

                if command == ":saveas":
                    if len(parts) != 2:
                        raise SessionError("Usage: :saveas name")
                    session = session_store.save(context, parts[1])
                    _mark_session_saved(session_state, session)
                    print(f"Saved session '{session.name}' at {session.saved_at}")
                    continue

                if command == ":new":
                    force_requested = _command_force_requested(parts[1:])
                    arguments = _command_arguments(parts[1:])
                    if arguments:
                        raise SessionError("Usage: :new [--force]")
                    _ensure_clean_session(session_state, ":new", force_requested)
                    context, session_state = _start_new_session()
                    _configure_readline(context, session_store)
                    print("Started a new session.")
                    continue

                if command == ":reset":
                    force_requested = _command_force_requested(parts[1:])
                    arguments = _command_arguments(parts[1:])
                    if arguments:
                        raise SessionError("Usage: :reset [--force]")
                    _ensure_clean_session(session_state, ":reset", force_requested)
                    context.reset_user_state()
                    if session_state.current_name is not None:
                        _mark_session_dirty(session_state)
                    else:
                        session_state.dirty = False
                    _configure_readline(context, session_store)
                    print("Current session reset.")
                    continue

                if command == ":load":
                    force_requested = _command_force_requested(parts[1:])
                    arguments = _command_arguments(parts[1:])
                    if len(arguments) != 1:
                        raise SessionError("Usage: :load name [--force]")
                    _ensure_clean_session(session_state, ":load", force_requested)
                    context, session = session_store.load(arguments[0])
                    _mark_session_saved(session_state, session)
                    _configure_readline(context, session_store)
                    print(f"Loaded session '{session.name}' from {session.saved_at}")
                    continue

                if command == ":rename-session":
                    if len(parts) != 2:
                        raise SessionError("Usage: :rename-session name")
                    if session_state.current_name is None:
                        raise SessionError("No active saved session to rename.")
                    if session_state.dirty:
                        raise SessionError("Save changes before renaming the current session.")
                    session = session_store.rename(session_state.current_name, parts[1])
                    _mark_session_saved(session_state, session)
                    print(f"Renamed session to '{session.name}'.")
                    continue

                if command == ":delete":
                    if len(parts) != 3:
                        raise SessionError("Usage: :delete var|function|session name")
                    target, name = parts[1], parts[2]
                    if target == "var":
                        context.delete_variable(name)
                        _mark_session_dirty(session_state)
                        _configure_readline(context, session_store)
                        print(f"Deleted variable '{name}'.")
                        continue
                    if target == "function":
                        context.delete_function(name)
                        _mark_session_dirty(session_state)
                        _configure_readline(context, session_store)
                        print(f"Deleted function '{name}'.")
                        continue
                    if target == "session":
                        session_store.delete(name)
                        if session_state.current_name == name:
                            session_state.current_name = None
                            session_state.last_saved_at = None
                            session_state.dirty = True
                        print(f"Deleted session '{name}'.")
                        continue
                    raise SessionError("Usage: :delete var|function|session name")

                print(f"Error: Unknown command '{line}'. Type :help for available commands.")
            except SessionError as error:
                print(f"Error: {error}")
            continue

        try:
            result, context = evaluate_expression(line, context)
        except SlowCrunchError as error:
            print(f"Error: {error}")
            continue

        _mark_session_dirty(session_state)
        print(_render_value(result, display_settings, context.entries[-1].get("kind"), context.zero_tolerance))
