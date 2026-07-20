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
- built-in constants: `pi`, `e`, `i`
- `ans` for the last result
- complex numbers such as `2 + 3i` and `sqrt(-1)`
- user variable assignment such as `x = 2 * 5`
- user-defined functions such as `area(r) = pi * r ^ 2`
- `:clear`, `:delete`, `:functions`, `:history`, `:help`, `:load`, `:new`, `:rename-session`, `:reset`, `:save`, `:saveas`, `:sessions`, `:status`, and `:vars` commands
- history filtering with `:history text` and history replay with `:history !index`
- topic help such as `:help functions` and `:help vars`
- named or timestamped session save/load
- multi-statement programs separated by newline or `;`
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
Commands: :clear, :delete, :functions, :help, :history, :load, :new, :rename-session, :reset, :save, :saveas, :sessions, :status, :vars
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
>> sqrt(-1)
i
>> (2 + 3i) * (1 - i)
5.0 + i
>> :history area
3: area(r) = pi * r ^ 2 = Defined area(r)
4: area(radius) = 78.53981633974483
>> :history !3
Replaying #3: area(r) = pi * r ^ 2
Defined area(r)
>> :save demo
Saved session 'demo' at 2026-07-20T12:34:56+02:00
>> :status
Session: demo
Saved at: 2026-07-20T12:34:56+02:00
Modified: no
User variables: 1
User functions: 1
History entries: 5
Numeric results: 3
>> :sessions
demo  2026-07-20T12:34:56+02:00
>> :load demo
Loaded session 'demo' from 2026-07-20T12:34:56+02:00
>> :rename-session geometry
Renamed session to 'geometry'.
>> :delete function area
Deleted function 'area'.
>> :reset
Current session reset.
>> :history
No history yet.
>> radius = 5;
.. area(r) = pi * r ^ 2;
.. area(radius)
78.53981633974483
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
- a richer terminal experience closer to SpeedCrunch

## Session Storage

Saved sessions are written as JSON files in `.slowcrunch-sessions/` by default.

Examples:

```text
:history
:history area
:history !3
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
:new
:status
:reset
:saveas demo
:rename-session geometry
:delete var radius
:delete function area
:delete session demo
```

`:clear` only clears the screen.  
`:new` starts a fresh unnamed session.  
`:status` prints the current session name, last save time, dirty state, and counts.  
`:reset` clears the in-memory session state.  
`:delete` removes an explicit target and never guesses what should be deleted.

## History Commands

Use `:history` to inspect or reuse previous entries:

```text
:history
:history area
:history !3
```

`:history` lists recorded expressions and their rendered results.  
`:history text` filters by expression or rendered result.  
`:history !index` replays the selected entry in the current session.

## Multi-Statement Input

slowcrunch can evaluate a small line-based program instead of a single statement.

- Separate statements with a newline or `;`
- The result of the block is the result of the last statement
- In the REPL, a trailing `;` keeps the input open and switches to the `.. ` continuation prompt

Example:

```text
>> radius = 5;
.. area(r) = pi * r ^ 2;
.. area(radius)
78.53981633974483
```
