import shlex
from dataclasses import dataclass

try:
    import readline
except ImportError:  # pragma: no cover
    readline = None

from slowcrunch.core.errors import IncompleteInputError, SessionError, SlowCrunchError
from slowcrunch.engine import evaluate_expression, parse_input
from slowcrunch.runtime.context import EvaluationContext
from slowcrunch.runtime.numbers import ANGLE_FORMAT_MODES, FORMAT_MODES, format_value
from slowcrunch.runtime.session_store import SessionStore
from slowcrunch.runtime.variable_store import SUPPORTED_VARIABLE_FORMATS, VariableStore

REPL_COMMANDS = (
    ":angles",
    ":clear",
    ":delete",
    ":format",
    ":functions",
    ":head",
    ":help",
    ":history",
    ":import-vars",
    ":load",
    ":load-vars",
    ":new",
    ":rename-session",
    ":reset",
    ":save",
    ":save-vars",
    ":saveas",
    ":sessions",
    ":show",
    ":status",
    ":tail",
    ":tolerance",
    ":vars",
)
REPL_KEYWORDS = ("exit", "quit")
HELP_TOPICS = (
    "basics", "functions", "statistics", "matrices", "vectors", "systems", "geometry",
    "angles", "clear", "delete", "format", "head", "history", "new", "reset",
    "sessions", "show", "status", "tail", "tolerance", "vars",
)
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
    elif _command_expects_variable_name(stripped_buffer, text):
        pool = context.variable_names()
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


def _command_expects_variable_name(line_buffer, text):
    if text.startswith(":"):
        return False

    prefixes = (":show ", ":head ", ":tail ")
    if not any(line_buffer.startswith(prefix) for prefix in prefixes):
        return False

    tokens = line_buffer.split()
    return len(tokens) <= 2


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


def _is_linreg_expression(expression, value):
    if not isinstance(value, list) or len(value) != 2:
        return False
    normalized = expression.strip()
    if "=" in normalized:
        normalized = normalized.split("=", 1)[1].strip()
    return normalized.startswith("linreg(")


def _render_list_lines(value, display_settings, zero_tolerance):
    inline_items = [
        _render_value(item, display_settings, None, zero_tolerance)
        for item in value
    ]
    inline = f"list[{len(value)}] [{', '.join(inline_items)}]"
    if len(value) <= 4 and len(inline) <= 72 and all(not isinstance(item, list) for item in value):
        return [inline]

    lines = [f"list[{len(value)}]"]
    for index, item in enumerate(value):
        item_lines = _render_value_lines(item, display_settings, None, zero_tolerance)
        lines.append(f"  [{index}] {item_lines[0]}")
        for continuation in item_lines[1:]:
            lines.append(f"      {continuation}")
    return lines


def _render_value_lines(value, display_settings, kind=None, zero_tolerance=None, expression=None):
    tolerance = zero_tolerance if zero_tolerance is not None else 0.0

    if _is_linreg_expression(expression or "", value):
        slope = _render_value(value[0], display_settings, None, tolerance)
        intercept = _render_value(value[1], display_settings, None, tolerance)
        return [f"linreg[slope={slope}, intercept={intercept}]"]

    if isinstance(value, list):
        return _render_list_lines(value, display_settings, tolerance)

    return [_render_value(value, display_settings, kind, tolerance)]


def _print_variables(context, display_settings):
    variables = context.user_variables()
    if not variables:
        print("No user variables.")
        return
    for name in sorted(variables):
        rendered_lines = _render_value_lines(
            variables[name],
            display_settings,
            context.get_variable_kind(name),
            context.zero_tolerance,
        )
        print(f"{name} = {rendered_lines[0]}")
        for continuation in rendered_lines[1:]:
            print(f"  {continuation}")


def _variable_value_lines(context, display_settings, name, expression=None):
    try:
        value = context.get_variable(name)
    except SlowCrunchError as error:
        raise SessionError(str(error)) from error

    resolved_expression = expression
    if resolved_expression is None and name == "ans" and context.entries:
        resolved_expression = context.entries[-1]["expression"]

    return _render_value_lines(
        value,
        display_settings,
        context.get_variable_kind(name),
        context.zero_tolerance,
        resolved_expression or name,
    )


def _parse_count_argument(value):
    try:
        count = int(value)
    except ValueError as error:
        raise SessionError("Count must be a non-negative integer.") from error
    if count < 0:
        raise SessionError("Count must be a non-negative integer.")
    return count


def _list_slice_lines(context, display_settings, name, count, from_tail=False):
    try:
        value = context.get_variable(name)
    except SlowCrunchError as error:
        raise SessionError(str(error)) from error

    if not isinstance(value, list):
        raise SessionError(f"Variable '{name}' is not a list.")

    sliced = value[-count:] if from_tail and count else value[:count]
    label = "tail" if from_tail else "head"
    expression = f"{label}({name}, {count})"
    return _render_value_lines(
        sliced,
        display_settings,
        None,
        context.zero_tolerance,
        expression,
    )


def _print_named_value(label, rendered_lines):
    print(f"{label} = {rendered_lines[0]}")
    for continuation in rendered_lines[1:]:
        print(f"  {continuation}")


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

    lines = []
    for index, entry in entries:
        rendered_lines = _render_value_lines(
            entry["result"],
            display_settings,
            entry.get("kind"),
            context.zero_tolerance,
            entry["expression"],
        )
        lines.append(f"{index}: {entry['expression']} = {rendered_lines[0]}")
        for continuation in rendered_lines[1:]:
            lines.append(f"   {continuation}")
    return lines


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
            ":head NAME [COUNT] Show the first items of a list variable.",
            ":help [topic] Show general help or help for a topic.",
            ":history [text|!index] Show, filter, or replay history.",
            ":import-vars PATH [FORMAT] Merge variables from a JSON or CSV file.",
            ":load NAME Load a saved session.",
            ":load-vars PATH [FORMAT] Replace user variables from a JSON or CSV file.",
            ":new      Start a new empty session.",
            ":rename-session NAME Rename the current saved session.",
            ":reset    Reset the current in-memory session.",
            ":save [NAME] Save the current session.",
            ":save-vars PATH [FORMAT] Write user variables to a JSON or CSV file.",
            ":saveas NAME Save the current session under a new name.",
            ":sessions List saved sessions.",
            ":show NAME Show a variable or structured result with TUI formatting.",
            ":status   Show the current session state.",
            ":tail NAME [COUNT] Show the last items of a list variable.",
            ":tolerance [VALUE] Show or change the zero tolerance.",
            ":vars    Show user-defined variables.",
            "quit     Exit the application.",
            "exit     Exit the application.",
            "Function topics: functions, statistics, matrices, vectors, systems, geometry.",
            "Command topics: angles, basics, clear, delete, format, head, history, new, reset, sessions, show, status, tail, tolerance, vars.",
            "Use # for end-of-line comments in expressions and commands.",
            "Examples:",
            "  :help angles",
            "  :help delete",
            "  :help format",
            "  :help functions",
            "  :help statistics",
            "  :help matrices",
            "  :help systems",
            "  :help geometry",
            "  :help show",
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
            "Use # to add an end-of-line comment or a full comment line.",
            "Built-in constants include pi, e, and i.",
            "The ans variable stores the last evaluated value.",
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
            "  2 + 2 # quick check",
            "  # temporary note",
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
        return [
            "Help: functions",
            "Use a focused topic for detailed help on a group of related functions.",
            "  :help statistics  List statistics and regression.",
            "  :help matrices    Matrix construction and operations.",
            "  :help vectors     Vector operations.",
            "  :help systems     Linear systems and least-squares fitting.",
            "  :help geometry    Explicit two-dimensional transformations.",
            "Several built-in functions accept complex arguments.",
            "Inverse trigonometric functions and arg return angle-typed results and follow :angles.",
            "Other categories: trigonometric, hyperbolic, exponential and logarithmic, complex, combinatorics, and formatting.",
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
            "  fact(5)",
            "  perm(5, 2)",
            "  comb(5, 2)",
            "  sqrt(-1)",
            "  conj(2 + 3i)",
            "  arg(i)",
            "  deg(pi / 2)",
            "  dms(pi / 6)",
            "  hms(4830)",
            "  area(5)",
            "  :functions",
        ]

    if topic == "statistics":
        return [
            "Help: statistics",
            "Use lists such as [1, 2, 3] as statistical data.",
            "Inspection: len, sum, min, max, mean, median, mode.",
            "Dispersion: variance, stdev, sample_variance, sample_stdev.",
            "Paired data: cov, sample_cov, corr, linreg.",
            "sum, mean, dispersion, covariance, and correlation accept complex values.",
            "min, max, median, mode, and linreg require real-number lists.",
            "Examples:",
            "  mean([1, 2, 4, 5])",
            "  sample_stdev([1, 2, 3])",
            "  corr([1, 2, 3], [2, 4, 6])",
            "  linreg([1, 2, 3], [2, 4, 6])",
        ]

    if topic == "matrices":
        return [
            "Help: matrices",
            "Use nested lists for matrices, such as [[1, 2], [3, 4]].",
            "Inspection: shape, rows, cols, transpose, trace, rank, rref.",
            "Construction: identity(n), diag(v).",
            "Operations: matmul(A, B), det(A), inv(A).",
            "Matrices must be non-empty, rectangular, and contain numeric values.",
            "det, inv, and trace require square matrices.",
            "Examples:",
            "  transpose([[1, 2, 3], [4, 5, 6]])",
            "  matmul([[1, 2]], [[3], [4]])",
            "  rref([[1, 2, -1], [2, 4, 0]])",
        ]

    if topic == "vectors":
        return [
            "Help: vectors",
            "Use lists such as [1, 2, 3] for vectors.",
            "dot(a, b) calculates the dot product of equally sized vectors.",
            "norm(v) returns Euclidean length and uses magnitudes for complex values.",
            "cross(a, b) calculates the cross product of two three-dimensional vectors.",
            "Examples:",
            "  dot([1, 2, 3], [4, 5, 6])",
            "  norm([3, 4])",
            "  cross([1, 0, 0], [0, 1, 0])",
        ]

    if topic == "systems":
        return [
            "Help: systems",
            "Use solve(A, b) to solve a square linear system with a unique solution.",
            "Put each equation's coefficients in one row of A and its constant in b.",
            "For 2x + y = 5 and x - y = 1, use:",
            "  solve([[2, 1], [1, -1]], [5, 1])",
            "The result [2, 1] means x = 2 and y = 1.",
            "Use rref(A) and rank(A) to inspect systems that may not have a unique solution.",
            "Use least_squares(A, b) for an overdetermined system or a best-fit linear model.",
            "least_squares requires at least as many rows as columns and independent columns.",
            "  least_squares([[1, 1], [1, 2], [1, 3]], [1, 2, 2])",
        ]

    if topic == "geometry":
        return [
            "Help: geometry",
            "rotate2d(angle) creates a two-dimensional counter-clockwise rotation matrix.",
            "scale2d(x, y) creates a two-dimensional scaling matrix.",
            "shear2d(xy, yx) creates a two-dimensional shear matrix.",
            "reflect2d(v) reflects across the line through the origin in direction v.",
            "apply(A, v) applies a matrix to a compatible vector.",
            "Angles use the usual calculator angle literals, such as 90deg or pi / 2.",
            "Examples:",
            "  apply(rotate2d(90deg), [1, 0])",
            "  apply(scale2d(2, 3), [4, 5])",
            "  apply(shear2d(2, 0), [1, 3])",
            "  apply(reflect2d([1, 0]), [2, 3])",
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
            "Use ans to reuse the last evaluated value.",
            "Examples:",
            "  10 / 2",
            "  ans + 3",
            "  :history",
            "  :history area",
            "  :history !3",
        ]

    if topic == "show":
        return [
            "Help: show",
            "Use :show name to render a variable with the same structured formatting used by the REPL.",
            "This is useful for long lists and structured results stored in variables such as ans.",
            "Examples:",
            "  :show values",
            "  :show ans",
        ]

    if topic == "head":
        return [
            "Help: head",
            "Use :head name [count] to show the first items of a list variable.",
            "If count is omitted, the default is 5.",
            "Examples:",
            "  :head values",
            "  :head values 3",
        ]

    if topic == "tail":
        return [
            "Help: tail",
            "Use :tail name [count] to show the last items of a list variable.",
            "If count is omitted, the default is 5.",
            "Examples:",
            "  :tail values",
            "  :tail values 3",
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
            "Use ans to reuse the last evaluated value.",
            "Use :save-vars path [json|csv] to export user variables to a file.",
            "Use :load-vars path [json|csv] [--force] to replace current user variables from a file.",
            "Use :import-vars path [json|csv] to merge variables from a file into the current session.",
            "CSV files use name, kind, and value columns; value is stored as compact JSON.",
            "Examples:",
            "  radius = 5",
            "  z = 2 + 3i",
            "  current = 4.7m",
            "  mass = 12 / 3",
            "  pi * radius ^ 2",
            "  :vars",
            "  :save-vars vars.json",
            "  :load-vars vars.csv --force",
            "  :import-vars vars.json",
        ]

    if topic == "sessions":
        return [
            "Help: sessions",
            "Every session is created and saved automatically after calculations and persistent changes.",
            "New automatic sessions use names such as slowcrunch-20260722-143000.",
            "Use :save [name] or :saveas name to choose the name used by later automatic saves.",
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
            "The status includes the active session name, last automatic save time, dirty state, numeric format mode, angle mode, zero tolerance, and object counts.",
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
        "Available topics: basics, functions, statistics, matrices, vectors, systems, geometry, angles, clear, delete, format, head, history, new, reset, sessions, show, status, tail, tolerance, vars",
    ]


def _print_help(topic=None):
    for line in _help_lines(topic):
        print(line)


def _clear_screen():
    print("\033[2J\033[H", end="")


def _parse_command(line):
    try:
        return shlex.split(line, comments=True)
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


def _autosave_session(context, session_store, session_state):
    try:
        session = session_store.save(context, session_state.current_name)
    except OSError as error:
        _mark_session_dirty(session_state)
        raise SessionError(f"Automatic session save failed: {error}") from error
    _mark_session_saved(session_state, session)
    return session


def _start_new_session(session_store):
    context = EvaluationContext()
    session_state = SessionState()
    _autosave_session(context, session_store, session_state)
    return context, session_state


def _variable_file_arguments(arguments, usage, allow_force=False):
    force_requested = _command_force_requested(arguments) if allow_force else False
    cleaned_arguments = _command_arguments(arguments) if allow_force else list(arguments)

    if len(cleaned_arguments) not in {1, 2}:
        raise SessionError(usage)

    path = cleaned_arguments[0]
    format_name = cleaned_arguments[1].lower() if len(cleaned_arguments) == 2 else None
    if format_name is not None and format_name not in SUPPORTED_VARIABLE_FORMATS:
        raise SessionError(usage)

    return path, format_name, force_requested


def _clear_user_variables(context):
    for name in tuple(context.user_variables()):
        context.delete_variable(name)


def _apply_variable_snapshot(context, variables, variable_kinds, replace=False):
    for name in variables:
        if name in context.protected_variables:
            raise SessionError(f"Protected variable cannot be imported: {name}")

    if replace:
        _clear_user_variables(context)

    for name, value in variables.items():
        context.set_variable(name, value, variable_kinds.get(name))


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


def run_repl(session_store=None, variable_store=None):
    display_settings = DisplaySettings()
    session_store = session_store or SessionStore()
    variable_store = variable_store or VariableStore()
    try:
        context, session_state = _start_new_session(session_store)
    except SessionError as error:
        print(f"Error: {error}")
        return
    _configure_readline(context, session_store)

    print("slowcrunch")
    print("Type an expression or 'quit' to exit.")
    print(
        "Commands: :angles, :clear, :delete, :format, :functions, :head, :help, :history, :import-vars, "
        ":load, :load-vars, :new, :rename-session, :reset, :save, :save-vars, :saveas, :sessions, "
        ":show, :status, :tail, :tolerance, :vars"
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

                if command == ":show":
                    if len(parts) != 2:
                        raise SessionError("Usage: :show name")
                    _print_named_value(parts[1], _variable_value_lines(context, display_settings, parts[1]))
                    continue

                if command == ":head":
                    if len(parts) not in {2, 3}:
                        raise SessionError("Usage: :head name [count]")
                    count = _parse_count_argument(parts[2]) if len(parts) == 3 else 5
                    _print_named_value(parts[1], _list_slice_lines(context, display_settings, parts[1], count))
                    continue

                if command == ":tail":
                    if len(parts) not in {2, 3}:
                        raise SessionError("Usage: :tail name [count]")
                    count = _parse_count_argument(parts[2]) if len(parts) == 3 else 5
                    _print_named_value(parts[1], _list_slice_lines(context, display_settings, parts[1], count, from_tail=True))
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
                    _autosave_session(context, session_store, session_state)
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
                        for rendered_line in _render_value_lines(
                            result,
                            display_settings,
                            context.entries[-1].get("kind"),
                            context.zero_tolerance,
                            entry["expression"],
                        ):
                            print(rendered_line)
                        _autosave_session(context, session_store, session_state)
                        continue

                    _print_history(context, display_settings, " ".join(parts[1:]))
                    continue

                if command == ":vars":
                    _print_variables(context, display_settings)
                    continue

                if command == ":sessions":
                    _print_sessions(session_store)
                    continue

                if command == ":save-vars":
                    path, format_name, _ = _variable_file_arguments(
                        parts[1:],
                        "Usage: :save-vars path [json|csv]",
                    )
                    variable_file = variable_store.save(context, path, format_name)
                    print(
                        f"Saved {variable_file.variable_count} variable(s) to {variable_file.path} "
                        f"as {variable_file.format_name}."
                    )
                    continue

                if command == ":import-vars":
                    path, format_name, _ = _variable_file_arguments(
                        parts[1:],
                        "Usage: :import-vars path [json|csv]",
                    )
                    variables, variable_kinds, variable_file = variable_store.load(path, format_name)
                    _apply_variable_snapshot(context, variables, variable_kinds, replace=False)
                    _autosave_session(context, session_store, session_state)
                    _configure_readline(context, session_store)
                    print(
                        f"Imported {variable_file.variable_count} variable(s) from {variable_file.path} "
                        f"as {variable_file.format_name}."
                    )
                    continue

                if command == ":load-vars":
                    path, format_name, force_requested = _variable_file_arguments(
                        parts[1:],
                        "Usage: :load-vars path [json|csv] [--force]",
                        allow_force=True,
                    )
                    _ensure_clean_session(session_state, ":load-vars", force_requested)
                    variables, variable_kinds, variable_file = variable_store.load(path, format_name)
                    _apply_variable_snapshot(context, variables, variable_kinds, replace=True)
                    _autosave_session(context, session_store, session_state)
                    _configure_readline(context, session_store)
                    print(
                        f"Loaded {variable_file.variable_count} variable(s) from {variable_file.path} "
                        f"as {variable_file.format_name}."
                    )
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
                    context, session_state = _start_new_session(session_store)
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
                    _autosave_session(context, session_store, session_state)
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
                        _autosave_session(context, session_store, session_state)
                        _configure_readline(context, session_store)
                        print(f"Deleted variable '{name}'.")
                        continue
                    if target == "function":
                        context.delete_function(name)
                        _autosave_session(context, session_store, session_state)
                        _configure_readline(context, session_store)
                        print(f"Deleted function '{name}'.")
                        continue
                    if target == "session":
                        session_store.delete(name)
                        if session_state.current_name == name:
                            session_state.current_name = None
                            session_state.last_saved_at = None
                            _autosave_session(context, session_store, session_state)
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

        if result is None:
            continue

        for rendered_line in _render_value_lines(
            result,
            display_settings,
            context.entries[-1].get("kind"),
            context.zero_tolerance,
            line,
        ):
            print(rendered_line)
        try:
            _autosave_session(context, session_store, session_state)
        except SessionError as error:
            print(f"Error: {error}")
