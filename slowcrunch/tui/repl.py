try:
    import readline
except ImportError:  # pragma: no cover
    readline = None

from slowcrunch.core.errors import SlowCrunchError
from slowcrunch.engine import evaluate_expression
from slowcrunch.runtime.context import EvaluationContext


def _configure_readline():
    if readline is None:
        return
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


def run_repl():
    context = EvaluationContext()
    _configure_readline()

    print("slowcrunch")
    print("Type an expression or 'quit' to exit.")
    print("Commands: :history, :vars")

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

        if line == ":history":
            _print_history(context)
            continue

        if line == ":vars":
            _print_variables(context)
            continue

        try:
            result, context = evaluate_expression(line, context)
        except SlowCrunchError as error:
            print(f"Error: {error}")
            continue

        print(result)
