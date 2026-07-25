class PipelineError(ValueError):
    """Base class for controlled pipeline failures."""


class MonetaryParseError(PipelineError):
    """Raised when a monetary value cannot be parsed without inference."""


class StateNormalizationError(PipelineError):
    """Raised when a state name does not match an explicit canonical alias."""


class ImportContractError(PipelineError):
    """Raised when a source file violates the controlled import contract."""


class ApprovalError(PipelineError):
    """Raised when an import cannot be explicitly approved."""
