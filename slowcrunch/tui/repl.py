try:
    import readline
except ImportError:  # pragma: no cover
    readline = None

from slowcrunch.core.errors import SlowCrunchError
from slowcrunch.engine import evaluate_expression
from slowcrunch.runtime.context import EvaluationContext

REPL_COMMANDS = (":functions", ":help", ":history", ":vars")
REPL_KEYWORDS = ("exit", "quit")
HELP_TOPICS = ("basics", "functions", "history", "vars")


def _completion_candidates(context, text, line_buffer="", begidx=0):
    stripped_buffer = line_buffer.lstrip()

    if stripped_buffer.startswith(":help ") and not text.startswith(":"):
        pool = HELP_TOPICS
    elif line_buffer.startswith(":") or text.startswith(":") or (begidx == 0 and text.startswith(":")):
        pool = REPL_COMMANDS
    else:
        function_candidates = [f"{name}(" for name in context.function_names()]
        variable_candidates = context.variable_names()
        pool = tuple(sorted(set(function_candidates + variable_candidates + list(REPL_KEYWORDS))))

    return [candidate for candidate in pool if candidate.startswith(text)]


def _make_completer(context):
    def completer(text, state):
        line_buffer = readline.get_line_buffer() if readline is not None else ""
        begidx = readline.get_begidx() if readline is not None else 0
        matches = _completion_candidates(context, text, line_buffer, begidx)
        if state < len(matches):
            return matches[state]
        return None

    return completer


def _configure_readline(context):
    if readline is None:
        return
    readline.set_completer_delims(" \t\n+-*/^()=,")
    readline.set_completer(_make_completer(context))
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind('"\\e[A": previous-history')
    readline.parse_and_bind('"\\e[B": next-history')


def _print_history(context):
    if not context.entries:
        print("No history yet.")
        return
    for index, entry in enumerate(context.entries, start=1):
        print(f"{index}: {entry['expression']} = {entry['result']}")


def _print_variables(context):
    variables = context.user_variables()
    if not variables:
        print("No user variables.")
        return
    for name in sorted(variables):
        print(f"{name} = {variables[name]}")


def _print_functions(context):
    functions = context.user_functions()
    if not functions:
        print("No user-defined functions.")
        return
    for name in sorted(functions):
        print(functions[name].signature())


def _help_lines(topic=None):
    if topic is None:
        return [
            "Available commands:",
            ":functions Show user-defined functions.",
            ":help [topic] Show general help or help for a topic.",
            ":history Show evaluated expressions and results.",
            ":vars    Show user-defined variables.",
            "quit     Exit the application.",
            "exit     Exit the application.",
            "Help topics: basics, functions, history, vars",
            "Examples:",
            "  :help functions",
            "  :help vars",
            "  2 + 3 * 4",
            "  radius = 5",
            "  area(r) = pi * r ^ 2",
        ]

    if topic == "basics":
        return [
            "Help: basics",
            "Enter expressions directly at the prompt.",
            "Supported operators: +, -, *, /, ^",
            "Use parentheses to group sub-expressions.",
            "Built-in constants include pi and e.",
            "The ans variable stores the last numeric result.",
            "Examples:",
            "  2 + 3 * 4",
            "  (1 + 2) * 3",
            "  sqrt(9) + cos(0)",
        ]

    if topic == "functions":
        return [
            "Help: functions",
            "Built-in functions include abs, sin, cos, tan, sqrt, and log.",
            "Define user functions with the form name(param1, param2) = expression.",
            "Function parameters are local to the function body.",
            "User-defined functions can reference global variables.",
            "Examples:",
            "  square(x) = x ^ 2",
            "  area(r) = pi * r ^ 2",
            "  area(5)",
            "  :functions",
        ]

    if topic == "history":
        return [
            "Help: history",
            "Use :history to list evaluated inputs and their results.",
            "The history includes assignments and function definitions.",
            "Use ans to reuse the last numeric result.",
            "Examples:",
            "  10 / 2",
            "  ans + 3",
            "  :history",
        ]

    if topic == "vars":
        return [
            "Help: vars",
            "Assign user variables with the form name = expression.",
            "Use :vars to list user-defined variables.",
            "Protected names such as ans, pi, and e cannot be reassigned.",
            "Examples:",
            "  radius = 5",
            "  mass = 12 / 3",
            "  pi * radius ^ 2",
            "  :vars",
        ]

    return [
        f"Unknown help topic '{topic}'.",
        "Available topics: basics, functions, history, vars",
    ]


def _print_help(topic=None):
    for line in _help_lines(topic):
        print(line)


def run_repl():
    context = EvaluationContext()
    _configure_readline(context)

    print("slowcrunch")
    print("Type an expression or 'quit' to exit.")
    print("Commands: :functions, :help, :history, :vars")

    while True:
        try:
            line = input(">> ").strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print("\nInterrupted.")
            break

        if not line:
            continue

        if line.lower() in {"quit", "exit"}:
            break

        if line.startswith(":help"):
            parts = line.split(maxsplit=1)
            topic = parts[1].strip() if len(parts) > 1 else None
            _print_help(topic)
            continue

        if line == ":functions":
            _print_functions(context)
            continue

        if line == ":history":
            _print_history(context)
            continue

        if line == ":vars":
            _print_variables(context)
            continue

        if line.startswith(":"):
            print(f"Error: Unknown command '{line}'. Type :help for available commands.")
            continue

        try:
            result, context = evaluate_expression(line, context)
        except SlowCrunchError as error:
            print(f"Error: {error}")
            continue

        print(result)
