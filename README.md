# slowcrunch

`slowcrunch` is a scientific calculator for the terminal, inspired by the SpeedCrunch workflow and user experience.

This project is specifically inspired by [SpeedCrunch](https://gitlab.com/heldercorreia/speedcrunch), both as a user-facing reference and as a long-term source of ideas for interaction design and calculator behavior.
slowcrunch does not reuse or derive from the SpeedCrunch source code; it is an original implementation inspired by the workflow and user experience.

It is being built with three priorities in mind:

- a fast, terminal-first user experience
- a compact, standard-library-first codebase
- a modular architecture that can grow without turning into a monolith

slowcrunch is already useful as a daily calculator, but it is still an evolving project rather than a finished SpeedCrunch-compatible clone.

## Highlights

- terminal REPL with multi-line input, history replay, and structured result rendering
- scientific, engineering, and SI-prefix output modes
- explicit support for angles, durations, complex numbers, and list values
- built-in functions for trigonometry, logarithms, statistics, combinatorics, and formatting
- user variables, user-defined functions, and reusable sessions
- standalone variable import and export in JSON and CSV
- explicit parsing and evaluation without `eval()`

## Features

slowcrunch currently provides:

- arithmetic expressions
- operator precedence and parentheses
- unary `+` and `-`
- exponentiation with `^`
- scientific notation such as `1.2e6`
- SI-prefix literals such as `10k`, `1M`, `220u`, `3f`, and `2a`
- explicit angle literals such as `90deg`, `1.5rad`, and `2mrad`
- compact pi-multiple angle literals such as `2pi` and `0.5pi`
- explicit duration literals such as `1h 20m 30s`, `45min`, and `90s`
- list literals such as `[1, 2, 3]`
- built-in functions across trigonometric, inverse trigonometric, hyperbolic, logarithmic, complex, statistics, and formatting categories
- built-in constants: `pi`, `e`, `i`
- `ans` for the last evaluated value
- complex numbers such as `2 + 3i` and `sqrt(-1)`
- user variable assignment such as `x = 2 * 5`
- user-defined functions such as `area(r) = pi * r ^ 2`
- `:angles`, `:clear`, `:delete`, `:format`, `:functions`, `:head`, `:help`, `:history`, `:import-vars`, `:load`, `:load-vars`, `:new`, `:rename-session`, `:reset`, `:save`, `:save-vars`, `:saveas`, `:sessions`, `:show`, `:status`, `:tail`, `:tolerance`, and `:vars` commands
- history filtering with `:history text` and history replay with `:history !index`
- output modes: `plain`, `scientific`, `engineering`, and `si`
- hierarchical topic help such as `:help statistics`, `:help matrices`, `:help vectors`, `:help systems`, `:help geometry`, and `:help vars`
- automatic session persistence after every calculation and named or timestamped session save/load
- variable export, import, and load in JSON or CSV
- multi-statement programs separated by newline or `;`
- keyboard history support through `readline` when available

## Project Layout

```text
slowcrunch/
  core/       tokenizer, parser, AST, evaluator, errors
  runtime/    built-ins and evaluation context
  tui/        terminal REPL
scripts/      helper scripts such as demo recording
demos/        asciinema recordings and related assets
tests/        automated tests for the engine
```

## Installation

Install `slowcrunch` as a normal CLI command:

```bash
python3 -m pip install .
```

For editable development installs:

```bash
python3 -m pip install -e .
```

You can also install it with tool-oriented workflows such as:

```bash
uv tool install .
pipx install .
```

After installation, launch the calculator with:

```bash
slowcrunch
```

For repeatable local packaging workflows, the repository also includes:

```bash
python3 scripts/build_dist.py
python3 scripts/install_local.py
python3 scripts/bump_version.py
python3 scripts/release.py
```

## Quick Start

Launch the TUI from a source checkout:

```bash
python3 -m slowcrunch
```

Build distributable artifacts:

```bash
python3 -m pip install build
python3 -m build
```

Or use the repository helper:

```bash
python3 scripts/build_dist.py
```

Run the test suite:

```bash
python3 -m unittest discover -v
```

## Distribution Notes

`slowcrunch` now supports standard Python packaging for an installable `slowcrunch` command on Linux, macOS, and Windows.

For future standalone binaries, the preferred direction is `PyOxidizer` with `python-build-standalone`, rather than direct Cosmopolitan integration. Cosmopolitan is a better fit for native C/C++ programs, while `slowcrunch` is a Python application.

See [docs/distribution.md](docs/distribution.md) for the current packaging and distribution strategy.

## Development Packaging Workflow

As the project evolves, the recommended local loop is:

1. Run the test suite.
2. Build the current source tree into a wheel and sdist.
3. Install the freshly built wheel into your user environment.
4. Launch `slowcrunch` from the installed command and test manually.

Commands:

```bash
python3 -m unittest discover -v
python3 scripts/build_dist.py
python3 scripts/install_local.py
slowcrunch
```

Notes:

- `scripts/build_dist.py` defaults to `--no-isolation`, which is useful on machines without network access after `build` and `setuptools` are already installed.
- `scripts/install_local.py` rebuilds by default, then force-reinstalls the newest wheel from `dist/`.
- Use `python3 scripts/install_local.py --editable` if you want an editable install for day-to-day development instead of testing the packaged wheel.

## Versioning and Release Helpers

The package version lives in [slowcrunch/__init__.py](slowcrunch/__init__.py) as `__version__`.
`pyproject.toml` reads that value dynamically when building distributions.

Show the current version:

```bash
python3 scripts/bump_version.py
```

Bump the version:

```bash
python3 scripts/bump_version.py --patch
python3 scripts/bump_version.py --minor
python3 scripts/bump_version.py --major
python3 scripts/bump_version.py --version 0.2.0
```

Run the local release workflow:

```bash
python3 scripts/release.py
```

That default workflow:

1. runs the test suite
2. builds a clean wheel and sdist in `dist/`
3. installs the freshly built wheel into your user environment

Useful variants:

```bash
python3 scripts/release.py --patch
python3 scripts/release.py --minor --skip-install
python3 scripts/release.py --editable
```

## Demo

GitHub does not render `.cast` files inline, so the preview below is an animated GIF generated from a real terminal session.

![slowcrunch demo preview](demos/slowcrunch-demo.gif)

An asciinema demo is included in the repository:

```bash
asciinema play demos/slowcrunch-demo.cast
```

Files:

- `demos/slowcrunch-demo.cast`
- `demos/slowcrunch-demo.gif`

The demo was recorded from a real `slowcrunch` session and showcases:

- numeric format switching
- angle output modes
- list inspection
- statistics and linear regression
- structured rendering with `:show ans`

## Example Session

```text
$ python3 -m slowcrunch
slowcrunch
Type an expression or 'quit' to exit.
Commands: :angles, :clear, :delete, :format, :functions, :head, :help, :history, :import-vars, :load, :load-vars, :new, :rename-session, :reset, :save, :save-vars, :saveas, :sessions, :show, :status, :tail, :tolerance, :vars
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
>> values = [1, 2 + 3, sqrt(16)]
[1.0, 5.0, 4.0]
>> values
[1.0, 5.0, 4.0]
>> len(values)
3.0
>> sum(values)
10.0
>> mean(values)
3.3333333333333335
>> median([1, 2, 4, 5])
3.0
>> mode([1, 1, 2])
1.0
>> variance([1, 2, 3])
0.6666666666666666
>> sample_stdev([1, 2, 3])
1.0
>> cov([1, 2, 3], [2, 4, 6])
1.3333333333333333
>> corr([1, 2, 3], [2, 4, 6])
1.0
>> linreg([1, 2, 3], [2, 4, 6])
linreg[slope=2.0, intercept=0.0]
>> :show ans
ans = linreg[slope=2.0, intercept=0.0]
>> values = [1, 2, 3, 4, 5]
list[5]
  [0] 1.0
  [1] 2.0
  [2] 3.0
  [3] 4.0
  [4] 5.0
>> :head values 3
values = list[3] [1.0, 2.0, 3.0]
>> :tail values 2
values = list[2] [4.0, 5.0]
>> fact(5)
120.0
>> perm(5, 2)
20.0
>> comb(5, 2)
10.0
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
Use a focused topic for detailed help on a group of related functions.
  :help statistics  List statistics and regression.
  :help matrices    Matrix construction and operations.
  :help vectors     Vector operations.
  :help systems     Linear systems and least-squares fitting.
  :help geometry    Explicit two-dimensional transformations.
Define user functions with the form name(param1, param2) = expression.
>> sqrt(-1)
i
>> (2 + 3i) * (1 - i)
5.0 + i
>> conj(2 + 3i)
2.0 - 3.0i
>> arg(i)
90deg
>> :angles rad
Angle format set to rad.
>> 2pi
6.28318530718rad
>> 360deg
6.28318530718rad
>> :angles dms
Angle format set to dms.
>> 90deg / 2
45deg 0' 0"
>> asin(1)
90deg 0' 0"
>> atan2(1, 1)
45deg 0' 0"
>> cot(45deg)
1.0
>> log10(1000)
3.0
>> deg(pi / 2)
90.0
>> dms(pi / 6)
30deg 0' 0"
>> hms(1h20m30s)
1h 20m 30s
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
>> sin(360deg)
-2.4492935982947064e-16
>> :tolerance 1e-12
Zero tolerance set to 1e-12.
>> sin(360deg)
0.0
>> :history area
3: area(r) = pi * r ^ 2 = Defined area(r)
4: area(radius) = 78.53981633974483
>> :history !3
Replaying #3: area(r) = pi * r ^ 2
Defined area(r)
>> :save demo
Saved session 'demo' at 2026-07-20T12:34:56+02:00
>> :save-vars vars.json
Saved 1 variable(s) to vars.json as json.
>> :delete var radius
Deleted variable 'radius'.
>> :import-vars vars.json
Imported 1 variable(s) from vars.json as json.
>> :save-vars vars.csv
Saved 1 variable(s) to vars.csv as csv.
>> :load-vars vars.csv --force
Loaded 1 variable(s) from vars.csv as csv.
>> :status
Session: demo
Saved at: 2026-07-20T12:34:56+02:00
Modified: no
Format: engineering
Angles: dms
Zero tolerance: 1e-12
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

- broader scientific function coverage and compatibility improvements
- richer TUI interaction and result browsing
- import/export for more user-defined state such as functions
- more polished documentation and onboarding

Longer-term goals:

- deeper SpeedCrunch-inspired workflow support
- scientific constants and advanced unit-oriented features
- a more capable terminal experience without losing code clarity

## Session Storage

Sessions are written as JSON files in `.slowcrunch-sessions/` by default. A new session is created automatically when the REPL starts and saved again after every calculation or persistent state change, so its expression history and results are retained.

Examples:

```text
:history
:history area
:history !3
:save
:save demo
:sessions
:load demo
:tolerance 1e-12
```

Automatic sessions use names such as `slowcrunch-20260722-143000`. If another session starts in the same second, slowcrunch adds a numeric suffix instead of overwriting it. Use `:save name` or `:saveas name` to select a descriptive name; later automatic saves continue to update that named session.

## Session Management Commands

Use these commands to manage the current interactive session:

```text
:clear
:new
:show ans
:head values 3
:tail values 3
:status
:tolerance
:tolerance 1e-12
:reset
:saveas demo
:rename-session geometry
:delete var radius
:delete function area
:delete session demo
```

`:clear` only clears the screen.  
`:new` starts and immediately saves a fresh timestamped session.
`:status` prints the current session name, last automatic save time, dirty state, format settings, zero tolerance, and counts.
`:tolerance` shows or changes the near-zero normalization threshold.  
`:reset` clears the in-memory session state.  
`:delete` removes an explicit target and never guesses what should be deleted.

## Variable Import And Export

User variables can be written to or read from standalone files without touching the full session state.

Examples:

```text
:save-vars vars.json
:save-vars vars.csv
:import-vars vars.json
:load-vars vars.csv --force
```

`:save-vars` exports only user-defined variables.  
`:import-vars` merges variables from a file into the current session.  
`:load-vars` replaces the current user variables and requires `--force` when the session is dirty.  
Formats are inferred from the file extension unless you pass `json` or `csv` explicitly.

JSON accepts two forms:

- native slowcrunch files with variable metadata
- plain JSON objects such as `{"radius": 5, "values": [1, 2, 3]}`

CSV uses one row per variable with these columns:

```text
name,kind,value
radius,,5.0
values,,[1.0,2.0,3.0]
bearing,angle,0.7853981633974483
```

The `value` column stores compact JSON so lists and complex values remain lossless.

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

Use `:angles` to control how angle-typed results are rendered:

```text
:angles
:angles deg
:angles dms
:angles rad
```

`deg` renders decimal degrees such as `45deg`.  
`dms` renders degrees, minutes, and seconds such as `45deg 0' 0"`.  
`rad` renders radians with a `rad` suffix such as `6.28318530718rad`.

Use `:tolerance` to control when very small numeric results are normalized to zero:

```text
:tolerance
:tolerance 1e-12
```

With a tolerance of `1e-12`, values such as `-2.4492935982947064e-16` are rendered and stored as `0.0`.

If you want a compact angle-typed multiple of `pi`, write `2pi` or `0.5pi`.  
If you want `2*pi` to stay angle-typed and follow `:angles`, write `360deg` or `2 * 180deg`.  
If you only need the numeric radian value, write `2 * pi`. `pi` is a built-in constant and radians are the internal angle unit.

Use explicit helper functions when you want angle or duration output instead of raw radians or seconds:

```text
deg(pi / 2)   = 90.0
dms(pi / 6)   = 30deg 0' 0"
hms(4830)     = 1h 20m 30s
```

## Supported Functions

slowcrunch currently includes these built-in function groups:

- Trigonometric: `sin`, `cos`, `tan`, `cot`, `sec`, `csc`
- Inverse trigonometric: `asin`, `acos`, `atan`, `atan2`, `acot`, `asec`, `acsc`, `arg`
- Hyperbolic: `sinh`, `cosh`, `tanh`, `coth`, `sech`, `csch`
- Inverse hyperbolic: `asinh`, `acosh`, `atanh`
- Exponential and logarithmic: `exp`, `ln`, `log`, `log10`, `log2`, `sqrt`
- Complex and utility: `abs`, `floor`, `ceil`, `re`, `im`, `conj`
- Statistics: `len`, `sum`, `min`, `max`, `mean`, `median`, `mode`, `variance`, `stdev`, `sample_variance`, `sample_stdev`, `cov`, `sample_cov`, `corr`, `linreg`
- Combinatorics: `fact`, `perm`, `comb`
- Linear algebra: `shape`, `rows`, `cols`, `transpose`, `dot`, `matmul`, `det`, `inv`, `solve`, `least_squares`, `identity`, `diag`, `trace`, `rank`, `rref`, `rotate2d`, `scale2d`, `shear2d`, `reflect2d`, `apply`
- Vector operations: `norm`, `cross`
- Formatting helpers: `deg`, `dms`, `hms`

Inverse trigonometric functions and `arg` return angle-typed results, so they follow the active `:angles` mode.
Statistics functions currently use list arguments such as `[1, 2, 3]`.
`sum`, `mean`, variance, standard deviation, covariance, and correlation accept complex values.
For complex inputs, variance and covariance use conjugate products; variance and standard deviation remain real and non-negative.
`min`, `max`, `median`, `mode`, and `linreg` remain limited to real-number lists.
`variance` and `stdev` use population formulas, while `sample_variance` and `sample_stdev` use sample formulas.
`cov` uses the population covariance formula, while `sample_cov` uses the sample covariance formula.
`mode` currently requires a unique mode.
`linreg(x, y)` returns `[slope, intercept]`.

## Lists

slowcrunch supports list literals as a basic collection type:

- `[1, 2, 3]`
- `values = [1, 2 + 3, sqrt(16)]`

Lists can be assigned to variables, shown in the REPL, and saved in sessions.
Arithmetic operators on lists are intentionally not supported yet.

Vectors use ordinary lists, while matrices use non-empty rectangular lists of numeric rows:

```text
shape([1, 2, 3])                    = [3]
shape([[1, 2], [3, 4]])             = [2, 2]
transpose([[1, 2], [3, 4]])         = [[1, 3], [2, 4]]
dot([1, 2, 3], [4, 5, 6])           = 32
matmul([[1, 2]], [[3], [4]])        = [[11]]
det([[4, 7], [2, 6]])                = 10
inv([[4, 7], [2, 6]])                = [[0.6, -0.7], [-0.2, 0.4]]
solve([[2, 1], [1, -1]], [5, 1])    = [2, 1]
identity(3)                           = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
diag([2, 3])                          = [[2, 0], [0, 3]]
trace([[1, 2], [3, 4]])              = 5
rank([[1, 2], [2, 4]])               = 1
rref([[1, 2, -1], [2, 4, 0]])        = [[1, 2, 0], [0, 0, 1]]
norm([3, 4])                          = 5
cross([1, 0, 0], [0, 1, 0])           = [0, 0, 1]
```

`rows`, `cols`, `transpose`, and `matmul` require matrices. `dot` requires equally sized vectors.
`det`, `inv`, and `solve` require square matrices; `solve(A, b)` requires one vector value per row of `A`.
`identity(n)` creates an `n` by `n` identity matrix, while `diag(v)` places vector `v` on a square matrix diagonal.
`trace(A)` requires a square matrix. `rank(A)` counts independent rows, and `rref(A)` returns reduced row echelon form.
`norm(v)` returns the Euclidean length of a vector. `cross(a, b)` requires two three-dimensional vectors.

## Geometric Transformations

Use explicit two-dimensional transformation matrices with `apply(A, v)`. `rotate2d(angle)` rotates counter-clockwise, `scale2d(x, y)` scales each axis independently, and `shear2d(xy, yx)` inclines each axis:

```text
apply(rotate2d(90deg), [1, 0]) = [0, 1]
apply(scale2d(2, 3), [4, 5])   = [8, 15]
apply(shear2d(2, 0), [1, 3])   = [7, 3]
apply(reflect2d([1, 0]), [2, 3]) = [2, -3]
```

`reflect2d(v)` reflects across the line through the origin in the non-zero direction `v`. For example, `[1, 0]` reflects across the x-axis.

## Solving Linear Systems

You can use `solve(A, b)` without prior matrix experience. Put the coefficients from each equation in one row of `A`, and put the constants on the right-hand side in `b`. The returned list follows the variable order used in the equations.

For example, solve this system for `x` and `y`:

```text
2x + y = 5
x - y = 1
```

The coefficients of `x` and `y` form the rows `[2, 1]` and `[1, -1]`; the constants form `[5, 1]`:

```text
solve([[2, 1], [1, -1]], [5, 1]) = [2, 1]
```

The result means `x = 2` and `y = 1`. `solve` reports an error when the system has no unique solution, or when the number of equations and unknowns does not match.

When observations give more equations than unknowns, use `least_squares(A, b)` to find the best-fitting solution. For example, fitting `y = a + bx` to the points `(1, 1)`, `(2, 2)`, and `(3, 2)`:

```text
least_squares([[1, 1], [1, 2], [1, 3]], [1, 2, 2]) = [0.6666666667, 0.5]
```

The result means `a` is approximately `0.667` and `b` is `0.5`. `least_squares` requires at least as many equations as unknowns and independent coefficient columns.

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

## Acknowledgements

Thanks to Helder Correia for creating [SpeedCrunch](https://gitlab.com/heldercorreia/speedcrunch) and publishing its source code.
That project is the main inspiration behind slowcrunch, while slowcrunch itself remains an original implementation.
