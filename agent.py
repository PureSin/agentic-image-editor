"""Shared agent error types used across the pipeline."""


class AgentError(Exception):
    """Raised when the agent cannot complete a run."""


class InsufficientBalanceError(AgentError):
    """Raised when the API returns a billing/quota error."""


class AuthenticationError(AgentError):
    """Raised when the API key is missing or rejected."""
