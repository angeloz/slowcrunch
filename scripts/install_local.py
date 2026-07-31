import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST_DIR = PROJECT_ROOT / "dist"


def _run(command):
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)


def _pip_install(arguments):
    base_command = [sys.executable, "-m", "pip", "install", "--user"]
    result = subprocess.run(
        base_command + arguments,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return

    fallback_command = base_command + ["--break-system-packages"] + arguments
    _run(fallback_command)


def _latest_wheel(dist_dir):
    wheels = sorted(dist_dir.glob("slowcrunch-*.whl"))
    if not wheels:
        raise FileNotFoundError(f"No slowcrunch wheel found in {dist_dir}")
    return wheels[-1]


def main():
    parser = argparse.ArgumentParser(
        description="Install the current slowcrunch build into the active user Python environment.",
    )
    parser.add_argument(
        "--dist-dir",
        default=str(DEFAULT_DIST_DIR),
        help="Directory containing built wheel artifacts.",
    )
    parser.add_argument(
        "--editable",
        action="store_true",
        help="Install the current source tree in editable mode instead of a wheel.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not build a fresh wheel before installation.",
    )
    parser.add_argument(
        "--isolation",
        action="store_true",
        help="Use isolated build environments when a build is needed.",
    )
    args = parser.parse_args()

    if args.editable:
        _pip_install(["--force-reinstall", "-e", "."])
        print("Installed slowcrunch in editable mode.")
        return 0

    dist_dir = Path(args.dist_dir).resolve()
    if not args.skip_build:
        build_command = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_dist.py"),
            "--output-dir",
            str(dist_dir),
        ]
        if args.isolation:
            build_command.append("--isolation")
        _run(build_command)

    wheel_path = _latest_wheel(dist_dir)
    _pip_install(["--force-reinstall", str(wheel_path)])
    print(f"Installed {wheel_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
