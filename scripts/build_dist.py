import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "dist"


def _run(command):
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(
        description="Build slowcrunch source and wheel distributions.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where build artifacts will be written.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete the output directory before building.",
    )
    parser.add_argument(
        "--isolation",
        action="store_true",
        help="Use isolated build environments instead of the default local backend install.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    if args.clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "build",
        "--outdir",
        str(output_dir),
    ]
    if not args.isolation:
        command.insert(3, "--no-isolation")

    _run(command)
    print(f"Built artifacts in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
