from slowcrunch.core.ast import AssignNode, BinaryOpNode, CallNode, NameNode, NumberNode, UnaryOpNode
from slowcrunch.core.errors import ParseError


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def parse(self):
        expression = self.parse_statement()
        if self.current().kind != "EOF":
            token = self.current()
            raise ParseError(f"Unexpected token '{token.value}' at position {token.position}.")
        return expression

    def parse_statement(self):
        if self.current().kind == "IDENT" and self.peek().kind == "ASSIGN":
            name = self.advance().value
            self.advance()
            return AssignNode(name, self.parse_expression())
        return self.parse_expression()

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
        node = self.parse_term()
        while self.current().kind == "OP" and self.current().value in {"+", "-"}:
            operator = self.advance().value
            node = BinaryOpNode(node, operator, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_power()
        while self.current().kind == "OP" and self.current().value in {"*", "/"}:
            operator = self.advance().value
            node = BinaryOpNode(node, operator, self.parse_power())
        return node

    def parse_power(self):
        node = self.parse_unary()
        if self.current().kind == "OP" and self.current().value == "^":
            operator = self.advance().value
            node = BinaryOpNode(node, operator, self.parse_power())
        return node

    def parse_unary(self):
        if self.current().kind == "OP" and self.current().value in {"+", "-"}:
            operator = self.advance().value
            return UnaryOpNode(operator, self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        token = self.current()

        if token.kind == "NUMBER":
            self.advance()
            return NumberNode(float(token.value))

        if token.kind == "IDENT":
            name = self.advance().value
            if self.match("LPAREN"):
                arguments = []
                if self.current().kind != "RPAREN":
                    while True:
                        arguments.append(self.parse_expression())
                        if not self.match("COMMA"):
                            break
                if not self.match("RPAREN"):
                    raise ParseError("Missing closing parenthesis in function call.")
                return CallNode(name, arguments)
            return NameNode(name)

        if self.match("LPAREN"):
            node = self.parse_expression()
            if not self.match("RPAREN"):
                raise ParseError("Missing closing parenthesis.")
            return node

        raise ParseError(f"Unexpected token '{token.value}' at position {token.position}.")
