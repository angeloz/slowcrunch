from dataclasses import dataclass

from slowcrunch.core.errors import TokenizeError


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
}


def tokenize(text):
    tokens = []
    index = 0

    while index < len(text):
        char = text[index]

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
            value = text[start:index]
            if dot_count > 1 or value == ".":
                raise TokenizeError(f"Invalid number at position {start}.")
            tokens.append(Token("NUMBER", value, start))
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
