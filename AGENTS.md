# AGENTS.md

Project name: `slowcrunch`

## Project Goal

Build `slowcrunch`, a scientific TUI calculator inspired by the SpeedCrunch user experience, while keeping the project lightweight, modular, and extensible.

## Core Constraints

- Keep the code compact and readable.
- Preserve the SpeedCrunch-like user experience in TUI form as closely as practical.
- Minimize external dependencies.
- Design a modular architecture that supports new features without rewriting the core.
- Develop incrementally, avoiding large multi-feature jumps.
- All project documentation, user-facing interface text, exposed commands, and code comments must be in English.
- Italian is used only for collaboration during development.

## Design Principles

- Keep the calculation engine clearly separated from the TUI.
- Avoid `eval()` and unsafe shortcuts: parsing and evaluation must be explicit.
- Prefer the standard library when it is sufficient.
- Introduce an external dependency only when it replaces a meaningful amount of complex or fragile code.
- Every new feature must be testable in isolation.

## Proposed Architecture

- `core/`: tokenizer, parser, AST, evaluator, execution context.
- `runtime/`: variables, user functions, constants, `ans` state, precision handling.
- `tui/`: input editor, history, result rendering, keyboard shortcuts.
- `tests/`: unit tests for parser/evaluator and integration tests for primary flows.

## Development Priorities

### Phase 1

- Basic REPL/TUI.
- Arithmetic expression evaluation.
- Operator precedence and parentheses.
- Essential scientific functions.
- History and reuse of the last result (`ans`).

### Phase 2

- User variables.
- User-defined functions.
- Autocompletion.
- Better error messages.

### Phase 3

- Scientific constants.
- Complex numbers.
- TUI UX improvements to move closer to the SpeedCrunch experience.

## Working Rules

- Implement one feature at a time.
- Write or update tests together with the feature.
- Keep the TUI as a thin layer above the core.
- Avoid tight coupling between parsing, evaluation, and rendering.
- Before adding dependencies, verify whether the requirement can be handled with simple local code.

## Distribution And Releases

- A source checkout from `main` is the latest development version, not the stable release channel.
- GitHub Releases are the official stable distribution channel for end users.
- Official release assets may include source distributions, wheels, and platform executables produced from tagged versions.
- GitHub Actions artifacts are temporary CI outputs and must not be treated as official releases.
- Package versions use the `X.Y.Z` format and official release tags use the matching `vX.Y.Z` format.

## Local Release Workflow

- Test the current development state with `python3 -m unittest discover -v`.
- Build local distribution artifacts with `python3 scripts/build_dist.py`.
- Install the current local build into the active environment with `python3 scripts/install_local.py`.
- Bump the package version with `python3 scripts/bump_version.py <version>`.
- Run the guided local release flow with `python3 scripts/release.py`.

## UX Goal

The TUI should feel fast from the keyboard, provide immediate feedback, maintain useful history, and support a natural input flow. The goal is not to copy the original graphical interface, but to reproduce its operational efficiency in the terminal.
