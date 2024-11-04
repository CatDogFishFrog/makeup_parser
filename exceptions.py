class AppError(Exception):
    """Base class for exceptions in this application."""
    pass

class ConfigError(AppError):
    """Raised for errors in the configuration."""
    pass

class FileNotFoundError(AppError):
    """Raised when input/output files are not found."""
    pass

class ParsingError(AppError):
    """Raised when parsing fails."""
    pass