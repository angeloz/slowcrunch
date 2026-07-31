import argparse
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = PROJECT_ROOT / "slowcrunch" / "__init__.py"
VERSION_PATTERN = re.compile(r'__version__ = "(\d+)\.(\d+)\.(\d+)"')


def parse_version(text):
    match = VERSION_PATTERN.search(text)
    if match is None:
        raise ValueError("Could not find __version__ assignment.")
    return tuple(int(part) for part in match.groups())


def parse_version_string(version_text):
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version_text)
    if match is None:
        raise ValueError("Version must use the form MAJOR.MINOR.PATCH.")
    return tuple(int(part) for part in match.groups())


def format_version(version):
    return ".".join(str(part) for part in version)


def bump_version(version, part):
    major, minor, patch = version
    if part == "major":
        return major + 1, 0, 0
    if part == "minor":
        return major, minor + 1, 0
    if part == "patch":
        return major, minor, patch + 1
    raise ValueError(f"Unsupported bump part: {part}")


def replace_version_text(text, version):
    current = VERSION_PATTERN.search(text)
    if current is None:
        raise ValueError("Could not find __version__ assignment.")
    replacement = f'__version__ = "{format_version(version)}"'
    return VERSION_PATTERN.sub(replacement, text, count=1)


def read_current_version(version_file=VERSION_FILE):
    return parse_version(version_file.read_text())


def write_version(version, version_file=VERSION_FILE):
    text = version_file.read_text()
    updated = replace_version_text(text, version)
    version_file.write_text(updated)


def main():
    parser = argparse.ArgumentParser(
        description="Show or update the slowcrunch package version.",
    )
    parser.add_argument(
        "--version",
        help="Set an explicit version in MAJOR.MINOR.PATCH form.",
    )
    parser.add_argument(
        "--major",
        action="store_true",
        help="Increment the major version and reset minor and patch to zero.",
    )
    parser.add_argument(
        "--minor",
        action="store_true",
        help="Increment the minor version and reset patch to zero.",
    )
    parser.add_argument(
        "--patch",
        action="store_true",
        help="Increment the patch version.",
    )
    args = parser.parse_args()

    current = read_current_version()
    requested_bumps = sum((args.major, args.minor, args.patch))
    if args.version is not None and requested_bumps:
        parser.error("--version cannot be combined with --major, --minor, or --patch.")
    if requested_bumps > 1:
        parser.error("Choose only one of --major, --minor, or --patch.")

    if args.version is not None:
        target = parse_version_string(args.version)
    elif args.major:
        target = bump_version(current, "major")
    elif args.minor:
        target = bump_version(current, "minor")
    elif args.patch:
        target = bump_version(current, "patch")
    else:
        print(format_version(current))
        return 0

    write_version(target)
    print(f"Updated version from {format_version(current)} to {format_version(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
