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
- scientific notation such as `1.2e6`
- SI-prefix literals such as `10k`, `1M`, `220u`, `3f`, and `2a`
- explicit angle literals such as `90deg`, `1.5rad`, and `2mrad`
- explicit duration literals such as `1h 20m 30s`, `45min`, and `90s`
- built-in functions: `abs`, `sin`, `cos`, `tan`, `sqrt`, `log`, `re`, `im`, `conj`, `arg`
- built-in constants: `pi`, `e`, `i`
- `ans` for the last result
- complex numbers such as `2 + 3i` and `sqrt(-1)`
- user variable assignment such as `x = 2 * 5`
- user-defined functions such as `area(r) = pi * r ^ 2`
- `:clear`, `:delete`, `:format`, `:functions`, `:history`, `:help`, `:load`, `:new`, `:rename-session`, `:reset`, `:save`, `:saveas`, `:sessions`, `:status`, and `:vars` commands
- history filtering with `:history text` and history replay with `:history !index`
- output modes: `plain`, `scientific`, `engineering`, and `si`
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
Commands: :clear, :delete, :format, :functions, :help, :history, :load, :new, :rename-session, :reset, :save, :saveas, :sessions, :status, :vars
>> 2 + 3 * 4
14.0
>> 10k + 25
10025.0
>> 3f * 2
6.0000000000000005e-15
>> sin(90deg)
1.0
>> 2mrad
0.002
>> 1h 20m 30s
4830.0
>> 45min
2700.0
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
>> conj(2 + 3i)
2.0 - 3.0i
>> arg(i)
1.5707963267948966
>> :format si
Output format set to si.
>> 10000
10k
>> 0.001
1m
>> :format engineering
Output format set to engineering.
>> 12000
12e3
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
Format: engineering
User variables: 1
User functions: 1
History entries: 8
Numeric results: 6
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

## Numeric Input And Output

slowcrunch accepts multiple numeric entry styles:

- plain decimals such as `12.5`
- scientific notation such as `1.2e6` or `4.7e-3`
- SI prefixes such as `10k`, `1M`, `220u`, `3f`, `2a`, `5T`, `1P`
- angle literals such as `90deg`, `1.5rad`, and `2mrad`
- duration literals such as `1h 20m 30s`, `45min`, `90s`, and `500ms`

SI prefixes are interpreted immediately as numeric values. For example:

```text
10k   = 10000
1M    = 1000000
1m    = 0.001
220u  = 0.00022
3f    = 0.000000000000003
2a    = 0.000000000000000002
```

Angle literals are also interpreted immediately:

```text
90deg  = pi / 2
1.5rad = 1.5
2mrad  = 0.002
```

Angles are stored internally in radians, so expressions like `sin(90deg)` and `sin(pi / 2)` are equivalent.

Durations are interpreted immediately as seconds:

```text
90s        = 90
45min      = 2700
1h20m30s   = 4830
500ms      = 0.5
```

Use `min` for standalone minutes. The short `m` form is also accepted inside composite durations such as `1h 20m 30s`.

Use `:format` to control numeric output rendering:

```text
:format
:format plain
:format scientific
:format engineering
:format si
```

`plain` keeps the default decimal rendering.  
`scientific` uses `mantissa e exponent`, such as `1.2e6`.  
`engineering` keeps exponents in steps of three, such as `12e3`.  
`si` uses engineering steps with SI prefixes, such as `12k` or `220u`.

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
