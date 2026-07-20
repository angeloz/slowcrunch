NUMERIC_TYPES = (int, float, complex)
ZERO_TOLERANCE = 1e-12


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


def format_value(value):
    normalized = normalize_number(value)
    if isinstance(normalized, complex):
        return _format_complex(normalized)
    return str(normalized)


def _format_complex(value):
    real = normalize_number(value.real)
    imag = normalize_number(value.imag)

    if real == 0.0:
        return _format_imaginary(imag)

    sign = "+" if imag > 0 else "-"
    return f"{real} {sign} {_format_imaginary(abs(imag))}"


def _format_imaginary(value):
    if value == 1.0:
        return "i"
    if value == -1.0:
        return "-i"
    return f"{value}i"
