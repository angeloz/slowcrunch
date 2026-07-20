import math

NUMERIC_TYPES = (int, float, complex)
ZERO_TOLERANCE = 1e-30
DEFAULT_SESSION_ZERO_TOLERANCE = 1e-12
FORMAT_MODES = ("plain", "scientific", "engineering", "si")
ANGLE_FORMAT_MODES = ("deg", "dms", "rad")
ANGLE_INPUT_UNITS = {
    "deg": math.pi / 180.0,
    "rad": 1.0,
}
DURATION_INPUT_UNITS = {
    "d": 86400.0,
    "h": 3600.0,
    "min": 60.0,
    "s": 1.0,
    "ms": 1e-3,
    "us": 1e-6,
    "ns": 1e-9,
}

SI_PREFIXES = {
    -30: "q",
    -27: "r",
    -24: "y",
    -21: "z",
    -18: "a",
    -15: "f",
    -12: "p",
    -9: "n",
    -6: "u",
    -3: "m",
    0: "",
    3: "k",
    6: "M",
    9: "G",
    12: "T",
    15: "P",
    18: "E",
    21: "Z",
    24: "Y",
    27: "R",
    30: "Q",
}

SI_INPUT_PREFIXES = {prefix: 10.0**exponent for exponent, prefix in SI_PREFIXES.items() if prefix}
SI_INPUT_PREFIXES["K"] = 1e3


def is_numeric(value):
    return isinstance(value, NUMERIC_TYPES)


def normalize_number(value, zero_tolerance=ZERO_TOLERANCE):
    if isinstance(value, bool) or not is_numeric(value):
        return value

    if isinstance(value, complex):
        real = 0.0 if abs(value.real) < zero_tolerance else float(value.real)
        imag = 0.0 if abs(value.imag) < zero_tolerance else float(value.imag)
        if imag == 0.0:
            return real
        return complex(real, imag)

    normalized = float(value)
    if abs(normalized) < zero_tolerance:
        return 0.0
    return normalized


def parse_number_literal(text):
    for duration_unit in sorted(DURATION_INPUT_UNITS, key=len, reverse=True):
        if not text.endswith(duration_unit):
            continue
        numeric_text = text[: -len(duration_unit)]
        try:
            value = float(numeric_text)
        except ValueError:
            continue
        return normalize_number(value * DURATION_INPUT_UNITS[duration_unit], 0.0)

    unit = next((name for name in ANGLE_INPUT_UNITS if text.endswith(name)), "")
    raw_text = text[: -len(unit)] if unit else text

    suffix = raw_text[-1] if raw_text and raw_text[-1] in SI_INPUT_PREFIXES else ""
    numeric_text = raw_text[:-1] if suffix else raw_text
    value = float(numeric_text)
    multiplier = SI_INPUT_PREFIXES.get(suffix, 1.0)
    unit_multiplier = ANGLE_INPUT_UNITS.get(unit, 1.0)
    return normalize_number(value * multiplier * unit_multiplier, 0.0)


def format_value(value, mode="plain", kind=None, angle_mode="deg", zero_tolerance=DEFAULT_SESSION_ZERO_TOLERANCE):
    if mode not in FORMAT_MODES:
        raise ValueError(f"Unknown format mode: {mode}")
    if angle_mode not in ANGLE_FORMAT_MODES:
        raise ValueError(f"Unknown angle format mode: {angle_mode}")

    normalized = normalize_number(value, zero_tolerance)
    if isinstance(normalized, list):
        formatted_items = [
            format_value(item, mode, None, angle_mode, zero_tolerance)
            for item in normalized
        ]
        return f"[{', '.join(formatted_items)}]"
    if not is_numeric(normalized):
        return str(normalized)
    if kind == "angle":
        return format_angle_value(normalized, angle_mode)
    if kind == "duration":
        return format_duration_hms(normalized)
    if isinstance(normalized, complex):
        return _format_complex(normalized, mode)
    return _format_real(normalized, mode)


def to_degrees(value):
    return normalize_number(math.degrees(value))


def format_angle_degrees(value):
    degrees = _rounded_display_number(to_degrees(value))
    return f"{_compact_decimal(degrees)}deg"


def format_angle_radians(value):
    return f"{_compact_decimal(normalize_number(value))}rad"


def format_angle_value(value, mode):
    if mode == "deg":
        return format_angle_degrees(value)
    if mode == "dms":
        return format_angle_dms(value)
    if mode == "rad":
        return format_angle_radians(value)
    raise ValueError(f"Unknown angle format mode: {mode}")


def format_angle_dms(value):
    total_seconds = abs(math.degrees(value)) * 3600.0
    degrees = int(total_seconds // 3600)
    remaining_seconds = total_seconds - (degrees * 3600)
    minutes = int(remaining_seconds // 60)
    seconds = _rounded_display_number(remaining_seconds - (minutes * 60))

    if seconds >= 60.0:
        seconds = 0.0
        minutes += 1
    if minutes >= 60:
        minutes = 0
        degrees += 1

    sign = "-" if value < 0 else ""
    return f"{sign}{degrees}deg {minutes}' {_compact_decimal(seconds)}\""


def format_duration_hms(value):
    total_seconds = abs(float(value))
    days = int(total_seconds // 86400)
    total_seconds -= days * 86400
    hours = int(total_seconds // 3600)
    total_seconds -= hours * 3600
    minutes = int(total_seconds // 60)
    seconds = _rounded_display_number(total_seconds - (minutes * 60))

    if seconds >= 60.0:
        seconds = 0.0
        minutes += 1
    if minutes >= 60:
        minutes = 0
        hours += 1
    if hours >= 24:
        hours = 0
        days += 1

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{_compact_decimal(seconds)}s")

    sign = "-" if value < 0 else ""
    return sign + " ".join(parts)


def _format_complex(value, mode):
    real = normalize_number(value.real)
    imag = normalize_number(value.imag)

    if real == 0.0:
        return _format_imaginary(imag, mode)

    sign = "+" if imag > 0 else "-"
    return f"{_format_real(real, mode)} {sign} {_format_imaginary(abs(imag), mode)}"


def _format_imaginary(value, mode):
    if value == 1.0:
        return "i"
    if value == -1.0:
        return "-i"
    return f"{_format_real(value, mode)}i"


def _format_real(value, mode):
    if mode == "plain":
        return str(value)
    if value == 0.0:
        return "0"
    if mode == "scientific":
        return _format_scientific(value)
    if mode == "engineering":
        return _format_engineering(value)
    if mode == "si":
        return _format_si(value)
    raise ValueError(f"Unknown format mode: {mode}")


def _format_scientific(value):
    mantissa, exponent = f"{value:.12e}".split("e")
    return f"{_compact_decimal(mantissa)}e{int(exponent)}"


def _format_engineering(value):
    exponent = _engineering_exponent(value)
    mantissa = normalize_number(value / (10.0**exponent))
    return f"{_compact_decimal(mantissa)}e{exponent}"


def _format_si(value):
    exponent = _engineering_exponent(value)
    prefix = SI_PREFIXES.get(exponent)
    if prefix is None:
        return _format_engineering(value)
    mantissa = normalize_number(value / (10.0**exponent))
    return f"{_compact_decimal(mantissa)}{prefix}"


def _engineering_exponent(value):
    return int(math.floor(math.log10(abs(value)) / 3.0) * 3)


def _compact_decimal(value):
    return f"{float(value):.12g}"


def _rounded_display_number(value):
    return normalize_number(float(_compact_decimal(value)))
