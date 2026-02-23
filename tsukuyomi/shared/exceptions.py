"""
Common exceptions for Tsukuyomi.

Hierarchy:
    TsukuyomiError (base)
    ├── AgentError (agent system errors)
    ├── EnvironmentError (environment system errors)
    ├── NarrativeError (narrative system errors)
    ├── ServiceError (external service errors)
    └── ValidationError (input validation errors)
"""


class TsukuyomiError(Exception):
    """Base exception for all Tsukuyomi errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class AgentError(TsukuyomiError):
    """Exception raised for agent system errors."""

    pass


class EnvironmentError(TsukuyomiError):
    """Exception raised for environment system errors."""

    pass


class NarrativeError(TsukuyomiError):
    """Exception raised for narrative system errors."""

    pass


class ServiceError(TsukuyomiError):
    """Exception raised for external service errors (LLM, database, vector store)."""

    pass


class ValidationError(TsukuyomiError):
    """Exception raised for input validation errors."""

    pass


class ConfigurationError(TsukuyomiError):
    """Exception raised for configuration errors."""

    pass


class TimeoutError(TsukuyomiError):
    """Exception raised when an operation times out."""

    pass
