class SlowCrunchError(Exception):
    """Base exception for slowcrunch."""


class TokenizeError(SlowCrunchError):
    """Raised when tokenization fails."""


class ParseError(SlowCrunchError):
    """Raised when parsing fails."""


class IncompleteInputError(ParseError):
    """Raised when parsing requires additional input."""


class EvaluationError(SlowCrunchError):
    """Raised when evaluation fails."""


class SessionError(SlowCrunchError):
    """Raised when session persistence fails."""
