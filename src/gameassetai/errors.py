class GameAssetAIError(Exception):
    """Base error for user-correctable GameAssetAI failures."""


class ValidationError(GameAssetAIError):
    """Raised when a document or filesystem contract is invalid."""


class SafetyError(GameAssetAIError):
    """Raised when an operation would cross a preservation boundary."""
