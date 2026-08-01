class SwanMPOError(Exception):
    """Base public error."""
class InputValidationError(SwanMPOError):
    """Raised when an input cannot be scored safely."""
