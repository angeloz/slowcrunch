import math

NUMERIC_TYPES = (int, float, complex)
ZERO_TOLERANCE = 1e-30
FORMAT_MODES = ("plain", "scientific", "engineering", "si")
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


def normalize_number(value):
    if isinstance(value, bool) or not is_numeric(value):
        return value

    if isinstance(value, complex):
        real = 0.0 if abs(value.real) < ZERO_TOLERANCE else float(value.real)
        imag = 0.0 if abs(value.imag) < ZERO_TOLERANCE else float(value.imag)
        if imag == 0.0:
            return real
        return complex(real, imag)

    normalized = float(value)
    if abs(normalized) < ZERO_TOLERANCE:
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
        return normalize_number(value * DURATION_INPUT_UNITS[duration_unit])

    unit = next((name for name in ANGLE_INPUT_UNITS if text.endswith(name)), "")
    raw_text = text[: -len(unit)] if unit else text

    suffix = raw_text[-1] if raw_text and raw_text[-1] in SI_INPUT_PREFIXES else ""
    numeric_text = raw_text[:-1] if suffix else raw_text
    value = float(numeric_text)
    multiplier = SI_INPUT_PREFIXES.get(suffix, 1.0)
    unit_multiplier = ANGLE_INPUT_UNITS.get(unit, 1.0)
    return normalize_number(value * multiplier * unit_multiplier)


def format_value(value, mode="plain"):
    if mode not in FORMAT_MODES:
        raise ValueError(f"Unknown format mode: {mode}")

    normalized = normalize_number(value)
    if isinstance(normalized, complex):
        return _format_complex(normalized, mode)
    return _format_real(normalized, mode)


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
