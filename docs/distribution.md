# Distribution

`slowcrunch` supports two distribution tracks:

- standard Python packaging for an installable `slowcrunch` CLI command
- future standalone binaries for users who do not want to manage Python themselves

## Installable CLI

The primary supported distribution path is standard Python packaging.

From a source checkout:

```bash
python3 -m pip install .
```

For development:

```bash
python3 -m pip install -e .
```

After installation, launch the REPL with:

```bash
slowcrunch
```

The source checkout path remains available:

```bash
python3 -m slowcrunch
```

## Build Artifacts

Build a wheel and source distribution with:

```bash
python3 -m pip install build
python3 -m build
```

This writes distributable artifacts to `dist/`.

For the project-local workflow, use:

```bash
python3 scripts/build_dist.py
```

That helper defaults to `--no-isolation`, which is convenient when the build backend is already installed locally and network access is unavailable.

## Install the Current Build

Install the latest wheel from `dist/` into the current user Python environment with:

```bash
python3 scripts/install_local.py
```

That helper rebuilds first, then force-reinstalls the newest wheel into the user site-packages for the active interpreter.

For editable installs:

```bash
python3 scripts/install_local.py --editable
```

## Standalone Binaries

Direct Cosmopolitan integration is not the primary plan for `slowcrunch`.
Cosmopolitan is a strong fit for native C/C++ programs, while `slowcrunch` is a Python application that currently runs on the standard interpreter.

If `slowcrunch` later gains self-contained binaries, the preferred direction is:

- `PyOxidizer` for packaging the application as a native launcher
- `python-build-standalone` for providing the embedded Python runtime

That future track should produce per-platform artifacts rather than promise one universal binary for every target OS.
