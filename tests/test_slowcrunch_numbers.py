import math
import unittest

from slowcrunch.runtime.numbers import format_value, parse_number_literal


class SlowCrunchNumbersTest(unittest.TestCase):
    def test_parse_si_kilo_literal(self):
        self.assertEqual(parse_number_literal("10k"), 10000.0)

    def test_parse_si_milli_literal(self):
        self.assertEqual(parse_number_literal("1m"), 0.001)

    def test_parse_scientific_literal(self):
        self.assertEqual(parse_number_literal("1.2e6"), 1200000.0)

    def test_parse_extended_si_literal(self):
        self.assertTrue(math.isclose(parse_number_literal("3f"), 3e-15))

    def test_parse_atto_literal(self):
        self.assertTrue(math.isclose(parse_number_literal("2a"), 2e-18))

    def test_parse_degree_literal(self):
        self.assertTrue(math.isclose(parse_number_literal("90deg"), math.pi / 2))

    def test_parse_radian_literal(self):
        self.assertEqual(parse_number_literal("1.5rad"), 1.5)

    def test_parse_milliradian_literal(self):
        self.assertEqual(parse_number_literal("2mrad"), 0.002)

    def test_parse_second_literal(self):
        self.assertEqual(parse_number_literal("90s"), 90.0)

    def test_parse_minute_literal(self):
        self.assertEqual(parse_number_literal("45min"), 2700.0)

    def test_parse_hour_literal(self):
        self.assertEqual(parse_number_literal("1h"), 3600.0)

    def test_format_plain_value(self):
        self.assertEqual(format_value(10000.0), "10000.0")

    def test_format_scientific_value(self):
        self.assertEqual(format_value(1200000.0, "scientific"), "1.2e6")

    def test_format_engineering_value(self):
        self.assertEqual(format_value(12000.0, "engineering"), "12e3")

    def test_format_si_value(self):
        self.assertEqual(format_value(10000.0, "si"), "10k")

    def test_format_small_si_value(self):
        self.assertEqual(format_value(0.001, "si"), "1m")

    def test_format_large_si_value(self):
        self.assertEqual(format_value(1e15, "si"), "1P")

    def test_format_complex_si_value(self):
        self.assertEqual(format_value(2e-6j, "si"), "2ui")


if __name__ == "__main__":
    unittest.main()
