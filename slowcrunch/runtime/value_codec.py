from slowcrunch.runtime.numbers import normalize_number


def encode_value(value):
    value = normalize_number(value)

    if isinstance(value, complex):
        return {
            "type": "complex",
            "real": value.real,
            "imag": value.imag,
        }

    if isinstance(value, list):
        return [encode_value(item) for item in value]

    if isinstance(value, dict):
        return {key: encode_value(item) for key, item in value.items()}

    return value


def decode_value(value):
    if isinstance(value, list):
        return [decode_value(item) for item in value]

    if isinstance(value, dict):
        if value.get("type") == "complex":
            return complex(value["real"], value["imag"])
        return {key: decode_value(item) for key, item in value.items()}

    return normalize_number(value)
