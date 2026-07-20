import math
import unittest

from slowcrunch.runtime.numbers import (
    format_angle_degrees,
    format_angle_dms,
    format_duration_hms,
    format_value,
    parse_number_literal,
    to_degrees,
)


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

    def test_convert_radians_to_degrees(self):
        self.assertEqual(to_degrees(math.pi / 2), 90.0)

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

    def test_format_text_value_is_mode_independent(self):
        self.assertEqual(format_value("Defined area(r)", "si"), "Defined area(r)")

    def test_format_list_value(self):
        self.assertEqual(format_value([1.0, 2e-6j, 3.5], "si"), "[1, 2ui, 3.5]")

    def test_format_angle_dms_value(self):
        self.assertEqual(format_angle_dms(math.pi / 6), '30deg 0\' 0"')

    def test_format_angle_degrees_value(self):
        self.assertEqual(format_angle_degrees(math.pi / 2), "90deg")

    def test_format_duration_hms_value(self):
        self.assertEqual(format_duration_hms(4830.0), "1h 20m 30s")

    def test_format_angle_value_with_kind(self):
        self.assertEqual(format_value(math.pi / 2, "plain", "angle"), "90deg")

    def test_format_angle_value_with_dms_mode(self):
        self.assertEqual(format_value(math.pi / 6, "plain", "angle", "dms"), '30deg 0\' 0"')

    def test_format_angle_value_with_rad_mode(self):
        self.assertEqual(format_value(math.pi / 2, "plain", "angle", "rad"), "1.57079632679rad")

    def test_format_duration_value_with_kind(self):
        self.assertEqual(format_value(19833.0, "plain", "duration"), "5h 30m 33s")


if __name__ == "__main__":
    unittest.main()
