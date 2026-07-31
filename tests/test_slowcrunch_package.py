import unittest
from unittest.mock import patch

import slowcrunch
from slowcrunch import __main__


class SlowCrunchPackageTest(unittest.TestCase):
    def test_package_exposes_version(self):
        self.assertEqual(slowcrunch.__version__, "0.1.0")

    def test_main_entry_point_runs_repl(self):
        with patch("slowcrunch.__main__.run_repl") as run_repl:
            exit_code = __main__.main()

        run_repl.assert_called_once_with()
        self.assertEqual(exit_code, 0)
