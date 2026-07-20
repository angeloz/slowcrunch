from slowcrunch.core.ast import (
    AssignNode,
    BinaryOpNode,
    CallNode,
    FunctionDefNode,
    ListNode,
    NameNode,
    NumberNode,
    ProgramNode,
    UnaryOpNode,
)
from slowcrunch.core.errors import IncompleteInputError, ParseError


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def parse(self):
        statements = self.parse_program()
        if self.current().kind != "EOF":
            raise ParseError(self._format_unexpected_token(self.current()))
        return ProgramNode(statements)

    def parse_program(self):
        statements = []
        self.skip_newlines()

        if self.current().kind == "EOF":
            raise IncompleteInputError("Unexpected end of expression.")

        while self.current().kind != "EOF":
            statements.append(self.parse_statement())

            if self.current().kind == "SEMI":
                self.advance()
                self.skip_newlines()
                if self.current().kind == "EOF":
                    raise IncompleteInputError("Expected another statement after ';'.")
                continue

            if self.current().kind == "NEWLINE":
                self.skip_newlines()
                continue

            break

        return statements

    def parse_statement(self):
        if self._is_function_definition():
            return self.parse_function_definition()
        if self.current().kind == "IDENT" and self.peek().kind == "ASSIGN":
            name = self.advance().value
            self.advance()
            return AssignNode(name, self.parse_expression())
        return self.parse_expression()

    def parse_function_definition(self):
        name = self.advance().value
        self.advance()
        parameters = []
        self.skip_newlines()
        if self.current().kind != "RPAREN":
            while True:
                if self.current().kind != "IDENT":
                    raise ParseError("Expected a parameter name in function definition.")
                parameters.append(self.advance().value)
                self.skip_newlines()
                if not self.match("COMMA"):
                    break
                self.skip_newlines()
        if not self.match("RPAREN"):
            if self.current().kind == "EOF":
                raise IncompleteInputError("Missing closing parenthesis in function definition.")
            raise ParseError("Missing closing parenthesis in function definition.")
        self.skip_newlines()
        if not self.match("ASSIGN"):
            if self.current().kind == "EOF":
                raise IncompleteInputError("Expected '=' after function definition.")
            raise ParseError("Expected '=' after function definition.")
        self.skip_newlines()
        return FunctionDefNode(name, parameters, self.parse_expression())

    def current(self):
        return self.tokens[self.index]

    def peek(self):
        return self.tokens[self.index + 1]

    def advance(self):
        token = self.current()
        self.index += 1
        return token

    def match(self, kind, value=None):
        token = self.current()
        if token.kind != kind:
            return None
        if value is not None and token.value != value:
            return None
        self.advance()
        return token

    def parse_expression(self):
        self.skip_newlines()
        node = self.parse_term()
        while self.current().kind == "OP" and self.current().value in {"+", "-"}:
            operator = self.advance().value
            self.skip_newlines()
            node = BinaryOpNode(node, operator, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_power()
        while self.current().kind == "OP" and self.current().value in {"*", "/"}:
            operator = self.advance().value
            self.skip_newlines()
            node = BinaryOpNode(node, operator, self.parse_power())
        return node

    def parse_power(self):
        node = self.parse_unary()
        if self.current().kind == "OP" and self.current().value == "^":
            operator = self.advance().value
            self.skip_newlines()
            node = BinaryOpNode(node, operator, self.parse_power())
        return node

    def parse_unary(self):
        self.skip_newlines()
        if self.current().kind == "OP" and self.current().value in {"+", "-"}:
            operator = self.advance().value
            self.skip_newlines()
            return UnaryOpNode(operator, self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        token = self.current()

        if token.kind == "NUMBER":
            self.advance()
            return NumberNode(float(token.value))

        if token.kind == "DURATION_NUMBER":
            self.advance()
            return NumberNode(float(token.value), "duration")

        if token.kind == "ANGLE_NUMBER":
            self.advance()
            return NumberNode(float(token.value), "angle")

        if token.kind == "IMAG_NUMBER":
            self.advance()
            return NumberNode(complex(0.0, float(token.value)))

        if token.kind == "IDENT":
            name = self.advance().value
            if self.match("LPAREN"):
                arguments = []
                self.skip_newlines()
                if self.current().kind != "RPAREN":
                    while True:
                        arguments.append(self.parse_expression())
                        self.skip_newlines()
                        if not self.match("COMMA"):
                            break
                        self.skip_newlines()
                if not self.match("RPAREN"):
                    if self.current().kind == "EOF":
                        raise IncompleteInputError("Missing closing parenthesis in function call.")
                    raise ParseError("Missing closing parenthesis in function call.")
                return CallNode(name, arguments)
            return NameNode(name)

        if self.match("LBRACKET"):
            items = []
            self.skip_newlines()
            if self.current().kind != "RBRACKET":
                while True:
                    items.append(self.parse_expression())
                    self.skip_newlines()
                    if not self.match("COMMA"):
                        break
                    self.skip_newlines()
            if not self.match("RBRACKET"):
                if self.current().kind == "EOF":
                    raise IncompleteInputError("Missing closing bracket in list literal.")
                raise ParseError("Missing closing bracket in list literal.")
            return ListNode(items)

        if self.match("LPAREN"):
            self.skip_newlines()
            node = self.parse_expression()
            self.skip_newlines()
            if not self.match("RPAREN"):
                if self.current().kind == "EOF":
                    raise IncompleteInputError("Missing closing parenthesis.")
                raise ParseError("Missing closing parenthesis.")
            return node

        raise ParseError(self._format_unexpected_token(token))

    def _format_unexpected_token(self, token):
        if token.kind == "EOF":
            return "Unexpected end of expression."
        if token.kind == "NEWLINE":
            return "Unexpected newline in expression."
        return f"Unexpected token '{token.value}' at position {token.position}."

    def skip_newlines(self):
        while self.current().kind == "NEWLINE":
            self.advance()

    def _is_function_definition(self):
        if self.current().kind != "IDENT" or self.peek().kind != "LPAREN":
            return False

        scan_index = self.index + 2
        token = self.tokens[scan_index]
        expect_parameter = token.kind != "RPAREN"

        while token.kind != "EOF":
            if token.kind == "RPAREN":
                return self.tokens[scan_index + 1].kind == "ASSIGN"
            if expect_parameter:
                if token.kind != "IDENT":
                    return False
                expect_parameter = False
            else:
                if token.kind != "COMMA":
                    return False
                expect_parameter = True
            scan_index += 1
            token = self.tokens[scan_index]

        return False
