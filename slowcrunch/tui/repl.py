try:
    import readline
except ImportError:  # pragma: no cover
    readline = None

from slowcrunch.core.errors import SlowCrunchError
from slowcrunch.engine import evaluate_expression
from slowcrunch.runtime.context import EvaluationContext

REPL_COMMANDS = (":help", ":history", ":vars")
REPL_KEYWORDS = ("exit", "quit")


def _completion_candidates(context, text, line_buffer="", begidx=0):
    if line_buffer.startswith(":") or text.startswith(":") or (begidx == 0 and text.startswith(":")):
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


def _print_help():
    print("Available commands:")
    print(":help    Show this help message.")
    print(":history Show evaluated expressions and results.")
    print(":vars    Show user-defined variables.")
    print("quit     Exit the application.")
    print("exit     Exit the application.")
    print("Examples:")
    print("  2 + 3 * 4")
    print("  radius = 5")
    print("  pi * radius ^ 2")


def run_repl():
    context = EvaluationContext()
    _configure_readline(context)

    print("slowcrunch")
    print("Type an expression or 'quit' to exit.")
    print("Commands: :help, :history, :vars")

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

        if line == ":help":
            _print_help()
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
