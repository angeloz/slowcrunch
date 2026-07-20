from dataclasses import dataclass

from slowcrunch.core.errors import TokenizeError
from slowcrunch.runtime.numbers import ANGLE_INPUT_UNITS, SI_INPUT_PREFIXES, parse_number_literal


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
    ",": "COMMA",
    ";": "SEMI",
}


def tokenize(text):
    tokens = []
    index = 0

    while index < len(text):
        char = text[index]

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

            is_imaginary = False
            if index < len(text) and text[index] == "i":
                next_index = index + 1
                if next_index == len(text) or not (text[next_index].isalnum() or text[next_index] == "_"):
                    is_imaginary = True
                    index += 1

            value = parse_number_literal(text[start:index - 1] if is_imaginary else text[start:index])
            tokens.append(Token("IMAG_NUMBER" if is_imaginary else "NUMBER", str(value), start))
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


def _match_angle_unit(text, index):
    for unit in sorted(ANGLE_INPUT_UNITS, key=len, reverse=True):
        end_index = index + len(unit)
        if text[index:end_index] == unit and (
            end_index == len(text) or not (text[end_index].isalnum() or text[end_index] == "_")
        ):
            return unit
    return None
