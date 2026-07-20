# slowcrunch

`slowcrunch` is a lightweight scientific calculator for the terminal, inspired by the SpeedCrunch workflow and user experience.

The project is intentionally being built in small steps:

- compact code
- minimal dependencies
- explicit parsing and evaluation
- modular architecture for future growth

## Current Status

The project currently provides a small REPL-based TUI with:

- arithmetic expressions
- operator precedence and parentheses
- unary `+` and `-`
- exponentiation with `^`
- built-in functions: `abs`, `sin`, `cos`, `tan`, `sqrt`, `log`
- built-in constants: `pi`, `e`
- `ans` for the last result
- user variable assignment such as `x = 2 * 5`
- `:history` and `:vars` commands
- keyboard history support through `readline` when available

This is an early foundation, not yet a full SpeedCrunch-compatible clone.

## Project Layout

```text
slowcrunch/
  core/       tokenizer, parser, AST, evaluator, errors
  runtime/    built-ins and evaluation context
  tui/        terminal REPL
tests/        automated tests for the engine
```

## Run

Launch the TUI:

```bash
python3 -m slowcrunch
```

Run the test suite:

```bash
python3 -m unittest discover -v
```

## Example Session

```text
$ python3 -m slowcrunch
slowcrunch
Type an expression or 'quit' to exit.
Commands: :history, :vars
>> 2 + 3 * 4
14.0
>> radius = 5
5.0
>> pi * radius ^ 2
78.53981633974483
>> :vars
radius = 5.0
>> :history
1: 2 + 3 * 4 = 14.0
2: radius = 5 = 5.0
3: pi * radius ^ 2 = 78.53981633974483
```

## Design Direction

- Keep the engine separate from the TUI.
- Avoid `eval()` and other unsafe shortcuts.
- Prefer the standard library unless a dependency clearly simplifies the design.
- Add one feature at a time and cover it with tests.

## Roadmap

Near-term priorities:

- better interactive input experience
- autocompletion for variables and functions
- improved error messages
- user-defined functions

Longer-term goals:

- scientific constants expansion
- complex numbers
- a richer terminal experience closer to SpeedCrunch
