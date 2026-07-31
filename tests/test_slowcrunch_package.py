import importlib.util
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import re

import slowcrunch
from slowcrunch import __main__


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_script_module(name):
    script_path = PROJECT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"tests_{name}", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SlowCrunchPackageTest(unittest.TestCase):
    def test_package_exposes_version(self):
        self.assertRegex(slowcrunch.__version__, r"^\d+\.\d+\.\d+$")

    def test_main_entry_point_runs_repl(self):
        with patch("slowcrunch.__main__.run_repl") as run_repl:
            exit_code = __main__.main()

        run_repl.assert_called_once_with()
        self.assertEqual(exit_code, 0)

    def test_bump_version_helpers(self):
        bump_version = _load_script_module("bump_version")
        self.assertEqual(bump_version.parse_version_string("1.2.3"), (1, 2, 3))
        self.assertEqual(bump_version.bump_version((1, 2, 3), "patch"), (1, 2, 4))
        self.assertEqual(bump_version.bump_version((1, 2, 3), "minor"), (1, 3, 0))
        self.assertEqual(bump_version.bump_version((1, 2, 3), "major"), (2, 0, 0))
        self.assertEqual(
            bump_version.replace_version_text('__version__ = "0.1.0"\n', (0, 1, 1)),
            '__version__ = "0.1.1"\n',
        )

    def test_bump_version_write_version_updates_temp_file(self):
        bump_version = _load_script_module("bump_version")
        with tempfile.TemporaryDirectory() as tempdir:
            version_file = Path(tempdir) / "__init__.py"
            version_file.write_text('__version__ = "0.1.0"\n')
            bump_version.write_version((0, 2, 0), version_file)
            self.assertEqual(version_file.read_text(), '__version__ = "0.2.0"\n')

    def test_release_command_plan_for_default_workflow(self):
        release = _load_script_module("release")
        commands = release.build_release_commands()
        self.assertEqual(commands[0], [release.sys.executable, "-m", "unittest", "discover", "-v"])
        self.assertEqual(commands[1][1:], [str(release.PROJECT_ROOT / "scripts" / "build_dist.py"), "--clean", "--output-dir", str(release.DEFAULT_OUTPUT_DIR.resolve())])
        self.assertEqual(commands[2][1:], [str(release.PROJECT_ROOT / "scripts" / "install_local.py"), "--skip-build", "--dist-dir", str(release.DEFAULT_OUTPUT_DIR.resolve())])

    def test_release_command_plan_for_patch_editable_workflow(self):
        release = _load_script_module("release")
        commands = release.build_release_commands(bump_part="patch", editable=True)
        self.assertEqual(commands[0], [release.sys.executable, str(release.PROJECT_ROOT / "scripts" / "bump_version.py"), "--patch"])
        self.assertEqual(commands[1], [release.sys.executable, "-m", "unittest", "discover", "-v"])
        self.assertEqual(commands[2], [release.sys.executable, str(release.PROJECT_ROOT / "scripts" / "install_local.py"), "--editable"])

    def test_release_tag_format_matches_package_version(self):
        release = _load_script_module("release")
        self.assertEqual(release.release_tag_for_version("0.2.0"), "v0.2.0")
        self.assertEqual(release.current_release_tag(), f"v{slowcrunch.__version__}")
