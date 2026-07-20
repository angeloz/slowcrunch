from dataclasses import dataclass


@dataclass(frozen=True)
class NumberNode:
    value: float


@dataclass(frozen=True)
class NameNode:
    name: str


@dataclass(frozen=True)
class UnaryOpNode:
    operator: str
    operand: object


@dataclass(frozen=True)
class BinaryOpNode:
    left: object
    operator: str
    right: object


@dataclass(frozen=True)
class CallNode:
    name: str
    arguments: list


@dataclass(frozen=True)
class AssignNode:
    name: str
    value: object


@dataclass(frozen=True)
class FunctionDefNode:
    name: str
    parameters: list
    body: object


@dataclass(frozen=True)
class ProgramNode:
    statements: list
