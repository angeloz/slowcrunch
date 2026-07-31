import math

from dataclasses import dataclass

from slowcrunch.core.errors import TokenizeError
from slowcrunch.runtime.numbers import (
    ANGLE_INPUT_UNITS,
    DURATION_INPUT_UNITS,
    SI_INPUT_PREFIXES,
    parse_number_literal,
)


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: int


SINGLE_CHAR_TOKENS = {
    "+": "OP",
    "-": "OP",
    "*": "OP",
    "/": "OP",
    "^": "OP",
    "=": "ASSIGN",
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ",": "COMMA",
    ";": "SEMI",
}


def tokenize(text):
    tokens = []
    index = 0

    while index < len(text):
        char = text[index]

        if char == "#":
            index = _skip_comment(text, index)
            continue

        if char == "\n":
            tokens.append(Token("NEWLINE", char, index))
            index += 1
            continue

        if char.isspace():
            index += 1
            continue

        if char in SINGLE_CHAR_TOKENS:
            tokens.append(Token(SINGLE_CHAR_TOKENS[char], char, index))
            index += 1
            continue

        if char.isdigit() or char == ".":
            start = index
            index = _scan_number_end(text, start)

            duration_match = _scan_duration_literal(text, start)
            if duration_match is not None:
                duration_end, duration_value = duration_match
                tokens.append(Token("DURATION_NUMBER", str(duration_value), start))
                index = duration_end
                continue

            pi_multiple_match = _scan_pi_multiple_literal(text, start, index)
            if pi_multiple_match is not None:
                pi_end, pi_value = pi_multiple_match
                tokens.append(Token("ANGLE_NUMBER", str(pi_value), start))
                index = pi_end
                continue

            suffix = ""
            unit = _match_angle_unit(text, index)
            if index < len(text) and text[index] in SI_INPUT_PREFIXES:
                prefixed_unit = _match_angle_unit(text, index + 1)
                if prefixed_unit is not None:
                    suffix = text[index]
                    index += 1
                    unit = prefixed_unit
                    index += len(unit)
                else:
                    next_index = index + 1
                    if next_index == len(text) or text[next_index] == "i" or not (
                        text[next_index].isalnum() or text[next_index] == "_"
                    ):
                        suffix = text[index]
                        index += 1

            if suffix == "" and unit is not None:
                index += len(unit)

            is_angle = unit is not None

            is_imaginary = False
            if index < len(text) and text[index] == "i":
                next_index = index + 1
                if next_index == len(text) or not (text[next_index].isalnum() or text[next_index] == "_"):
                    is_imaginary = True
                    index += 1

            value = parse_number_literal(text[start:index - 1] if is_imaginary else text[start:index])
            if is_imaginary:
                token_kind = "IMAG_NUMBER"
            elif is_angle:
                token_kind = "ANGLE_NUMBER"
            else:
                token_kind = "NUMBER"
            tokens.append(Token(token_kind, str(value), start))
            continue

        if char.isalpha() or char == "_":
            start = index
            while index < len(text) and (text[index].isalnum() or text[index] == "_"):
                index += 1
            tokens.append(Token("IDENT", text[start:index], start))
            continue

        raise TokenizeError(f"Invalid character '{char}' at position {index}.")

    tokens.append(Token("EOF", "", len(text)))
    return tokens


def _scan_number_end(text, start):
    index = start
    dot_count = 0
    while index < len(text) and (text[index].isdigit() or text[index] == "."):
        if text[index] == ".":
            dot_count += 1
        index += 1
    if dot_count > 1 or text[start:index] == ".":
        raise TokenizeError(f"Invalid number at position {start}.")

    if index < len(text) and text[index] in {"e", "E"}:
        exponent_index = index + 1
        if exponent_index < len(text) and text[exponent_index] in {"+", "-"}:
            exponent_index += 1
        exponent_start = exponent_index
        while exponent_index < len(text) and text[exponent_index].isdigit():
            exponent_index += 1
        if exponent_index == exponent_start:
            raise TokenizeError(f"Invalid scientific notation at position {start}.")
        index = exponent_index

    return index


def _scan_duration_literal(text, start):
    components = []
    index = start
    end_index = start

    while index < len(text) and (text[index].isdigit() or text[index] == "."):
        number_end = _scan_number_end(text, index)
        unit = _match_duration_unit(text, number_end)
        if unit is None:
            return None if not components else (end_index, sum(components))

        if unit == "m":
            component_value = float(text[index:number_end]) * 60.0
        else:
            component_value = parse_number_literal(text[index:number_end + len(unit)])
        components.append(component_value)

        end_index = number_end + len(unit)
        index = _skip_inline_whitespace(text, end_index)

    if not components:
        return None

    # Keep standalone `1m` as milli, not minute. The short `m` alias is accepted
    # only within a composite duration such as `1h 20m 30s`.
    if len(components) == 1 and text[start:end_index].endswith("m"):
        return None

    return end_index, sum(components)


def _scan_pi_multiple_literal(text, start, number_end):
    if text[number_end:number_end + 2] != "pi":
        return None

    end_index = number_end + 2
    if end_index < len(text) and (text[end_index].isalnum() or text[end_index] == "_"):
        return None

    multiplier = float(text[start:number_end])
    return end_index, multiplier * math.pi


def _match_angle_unit(text, index):
    for unit in sorted(ANGLE_INPUT_UNITS, key=len, reverse=True):
        end_index = index + len(unit)
        if text[index:end_index] == unit and (
            end_index == len(text) or not (text[end_index].isalnum() or text[end_index] == "_")
        ):
            return unit
    return None


def _match_duration_unit(text, index):
    units = tuple(sorted(tuple(DURATION_INPUT_UNITS) + ("m",), key=len, reverse=True))
    for unit in units:
        end_index = index + len(unit)
        if text[index:end_index] != unit:
            continue
        if end_index == len(text) or not (text[end_index].isalpha() or text[end_index] == "_"):
            return unit
    return None


def _skip_inline_whitespace(text, index):
    while index < len(text) and text[index].isspace() and text[index] != "\n":
        index += 1
    return index


def _skip_comment(text, index):
    while index < len(text) and text[index] != "\n":
        index += 1
    return index
