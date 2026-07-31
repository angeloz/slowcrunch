import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "dist"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bump_version


def _run(command):
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)


def release_tag_for_version(version):
    return f"v{version}"


def current_release_tag():
    return release_tag_for_version(
        bump_version.format_version(bump_version.read_current_version())
    )


def build_release_commands(
    *,
    version=None,
    bump_part=None,
    skip_tests=False,
    skip_install=False,
    editable=False,
    isolation=False,
    output_dir=DEFAULT_OUTPUT_DIR,
):
    commands = []

    if version is not None:
        commands.append(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "bump_version.py"), "--version", version]
        )
    elif bump_part is not None:
        commands.append(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "bump_version.py"), f"--{bump_part}"]
        )

    if not skip_tests:
        commands.append([sys.executable, "-m", "unittest", "discover", "-v"])

    if editable:
        if not skip_install:
            commands.append([sys.executable, str(PROJECT_ROOT / "scripts" / "install_local.py"), "--editable"])
        return commands

    build_command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "build_dist.py"),
        "--clean",
        "--output-dir",
        str(Path(output_dir).resolve()),
    ]
    if isolation:
        build_command.append("--isolation")
    commands.append(build_command)

    if not skip_install:
        commands.append(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "install_local.py"),
                "--skip-build",
                "--dist-dir",
                str(Path(output_dir).resolve()),
            ]
        )

    return commands


def main():
    parser = argparse.ArgumentParser(
        description="Run the local slowcrunch release workflow.",
    )
    parser.add_argument(
        "--version",
        help="Set an explicit version before running tests, build, and install.",
    )
    parser.add_argument(
        "--major",
        action="store_true",
        help="Increment the major version before running the workflow.",
    )
    parser.add_argument(
        "--minor",
        action="store_true",
        help="Increment the minor version before running the workflow.",
    )
    parser.add_argument(
        "--patch",
        action="store_true",
        help="Increment the patch version before running the workflow.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Do not run the unit test suite before building.",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Build the current release but do not install it into the local user environment.",
    )
    parser.add_argument(
        "--editable",
        action="store_true",
        help="Install the source tree in editable mode instead of building and installing a wheel.",
    )
    parser.add_argument(
        "--isolation",
        action="store_true",
        help="Use isolated build environments during packaging.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory used for built release artifacts.",
    )
    args = parser.parse_args()

    requested_bumps = sum((args.major, args.minor, args.patch))
    if args.version is not None and requested_bumps:
        parser.error("--version cannot be combined with --major, --minor, or --patch.")
    if requested_bumps > 1:
        parser.error("Choose only one of --major, --minor, or --patch.")

    bump_part = None
    if args.major:
        bump_part = "major"
    elif args.minor:
        bump_part = "minor"
    elif args.patch:
        bump_part = "patch"

    commands = build_release_commands(
        version=args.version,
        bump_part=bump_part,
        skip_tests=args.skip_tests,
        skip_install=args.skip_install,
        editable=args.editable,
        isolation=args.isolation,
        output_dir=args.output_dir,
    )
    for command in commands:
        _run(command)

    version = bump_version.format_version(bump_version.read_current_version())
    tag = release_tag_for_version(version)
    print(f"Current package version: {version}")
    print(f"Suggested release tag: {tag}")
    print("Official stable builds should be uploaded as GitHub Release assets.")
    print("GitHub Actions artifacts remain suitable only for temporary CI outputs.")
    print("Release workflow completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
