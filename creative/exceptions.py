"""
Creative Engine exceptions.

Domain-specific errors for the Creative Engine.

Hierarchy:

    CreativeError
    ├── TemplateError
    ├── BrandError
    ├── ValidationError
    └── RenderError
"""

from __future__ import annotations


class CreativeError(Exception):
    """
    Base class for all Creative Engine errors.

    Mirrors the role of AIValidationError in the AI pipeline: a
    single catchable type for the whole domain.
    """


class TemplateError(CreativeError):
    """
    Raised when a template cannot be located or identified.

    Covers missing templates, unreadable files, invalid JSON,
    duplicate template ids and missing meta.id values.
    """


class BrandError(CreativeError):
    """
    Raised when a brand profile cannot be located or identified.

    Covers missing profiles, unreadable files, invalid JSON and
    id/filename mismatches.
    """


class ValidationError(CreativeError):
    """
    Raised when a template or brand profile fails validation.

    Unlike TemplateError and BrandError, this indicates the data was
    found but does not conform to its schema or constraints.

    Attributes:
        errors:
            Optional list of human-readable field errors.
    """

    def __init__(
        self,
        message: str,
        errors: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.errors = errors or []


class RenderError(CreativeError):
    """
    Raised when a creative cannot be rendered.

    Covers missing content, unresolvable fonts or colors, unsupported
    zone styles and I/O failures while writing the output image.
    """
