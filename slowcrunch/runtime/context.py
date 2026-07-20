from difflib import get_close_matches
from dataclasses import dataclass, field

from slowcrunch.core.errors import EvaluationError
from slowcrunch.runtime.builtins import build_builtin_functions, build_builtin_variables


@dataclass
class EvaluationContext:
    variables: dict = field(default_factory=build_builtin_variables)
    functions: dict = field(default_factory=build_builtin_functions)
    history: list = field(default_factory=list)
    entries: list = field(default_factory=list)

    def __post_init__(self):
        self.protected_variables = {"ans", "e", "pi"}

    def get_variable(self, name):
        if name not in self.variables:
            suggestion = self._suggest_name(name, self.variables)
            if suggestion:
                raise EvaluationError(f"Unknown variable: {name}. Did you mean '{suggestion}'?")
            raise EvaluationError(f"Unknown variable: {name}")
        return self.variables[name]

    def get_function(self, name):
        if name not in self.functions:
            suggestion = self._suggest_name(name, self.functions)
            if suggestion:
                raise EvaluationError(f"Unknown function: {name}. Did you mean '{suggestion}'?")
            raise EvaluationError(f"Unknown function: {name}")
        return self.functions[name]

    def set_variable(self, name, value):
        if name in self.protected_variables:
            raise EvaluationError(f"Protected variable cannot be assigned: {name}")
        self.variables[name] = value

    def set_ans(self, value):
        self.variables["ans"] = value
        self.history.append(value)

    def record_entry(self, expression, result):
        self.entries.append({"expression": expression, "result": result})

    def user_variables(self):
        return {
            name: value
            for name, value in self.variables.items()
            if name not in self.protected_variables
        }

    def variable_names(self):
        return sorted(self.variables)

    def function_names(self):
        return sorted(self.functions)

    def _suggest_name(self, name, pool):
        matches = get_close_matches(name, pool, n=1, cutoff=0.5)
        if matches:
            return matches[0]
        return None
