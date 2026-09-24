"""Typed exceptions for the depth report system."""


class ProjectError(Exception):
    """Base exception for the project."""


class ConfigError(ProjectError):
    """Raised when configuration is missing or invalid."""


class DataReadError(ProjectError):
    """Raised when an input source cannot be read."""


class ValidationError(ProjectError):
    """Raised when input data fails validation."""


class ProcessingError(ProjectError):
    """Raised when comparison or metric calculation fails."""


class OutputError(ProjectError):
    """Raised when output generation fails."""
