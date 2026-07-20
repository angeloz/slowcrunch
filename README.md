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
- user-defined functions such as `area(r) = pi * r ^ 2`
- `:clear`, `:delete`, `:functions`, `:history`, `:help`, `:load`, `:reset`, `:save`, `:sessions`, and `:vars` commands
- topic help such as `:help functions` and `:help vars`
- named or timestamped session save/load
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
Commands: :clear, :delete, :functions, :help, :history, :load, :reset, :save, :sessions, :vars
>> 2 + 3 * 4
14.0
>> radius = 5
5.0
>> area(r) = pi * r ^ 2
Defined area(r)
>> area(radius)
78.53981633974483
>> pi * radius ^ 2
78.53981633974483
>> :vars
radius = 5.0
>> :functions
area(r)
>> :help functions
Help: functions
Built-in functions include abs, sin, cos, tan, sqrt, and log.
Define user functions with the form name(param1, param2) = expression.
>> :save demo
Saved session 'demo' at 2026-07-20T12:34:56+02:00
>> :sessions
demo  2026-07-20T12:34:56+02:00
>> :load demo
Loaded session 'demo' from 2026-07-20T12:34:56+02:00
>> :delete function area
Deleted function 'area'.
>> :reset
Current session reset.
>> :history
No history yet.
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

## Session Storage

Saved sessions are written as JSON files in `.slowcrunch-sessions/` by default.

Examples:

```text
:save
:save demo
:sessions
:load demo
```

If `:save` is called without a name, slowcrunch generates one from the current local date and time.

## Session Management Commands

Use these commands to manage the current interactive session:

```text
:clear
:reset
:delete var radius
:delete function area
:delete session demo
```

` :clear` only clears the screen.  
` :reset` clears the in-memory session state.  
` :delete` removes an explicit target and never guesses what should be deleted.
