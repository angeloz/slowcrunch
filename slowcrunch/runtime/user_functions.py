from dataclasses import dataclass


@dataclass(frozen=True)
class UserFunction:
    name: str
    parameters: tuple
    body: object

    def signature(self):
        return f"{self.name}({', '.join(self.parameters)})"
