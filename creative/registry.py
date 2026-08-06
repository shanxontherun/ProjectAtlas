"""
Template Registry.

Discovers, loads, validates and returns data-driven JSON templates
for the Creative Engine.

Templates are discovered from the template directory, identified by
their ``meta.id``, validated against the template contract and, when
they reference a brand, returned with the resolved brand profile
attached.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from creative._io import format_validation_errors, read_json
from creative.brands import BrandProfileLoader
from creative.exceptions import TemplateError, ValidationError
from creative.models import BrandProfile, Template


DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "templates"


class TemplateRegistry:
    """
    Registry of data-driven creative templates.

    Templates are loaded lazily and indexed once per process. An
    index entry only requires a readable ``meta.id``; full structural
    validation happens on load.
    """

    def __init__(
        self,
        template_dir: Path | None = None,
        brand_loader: BrandProfileLoader | None = None,
    ) -> None:
        self.template_dir = template_dir or DEFAULT_TEMPLATE_DIR
        self.brand_loader = brand_loader or BrandProfileLoader()
        self._index: dict[str, Path] | None = None

    def discover(self) -> list[str]:
        """
        Return the ids of all discoverable templates, sorted.

        Raises:
            TemplateError:
                If a template file is unreadable, missing ``meta.id``,
                or duplicates an existing id.
        """

        return sorted(self._build_index().keys())

    def load(
        self,
        template_id: str,
    ) -> Template:
        """
        Load, validate and return a template by id.

        When the template references a brand, the resolved brand
        profile is attached to ``Template.brand_profile``.

        Raises:
            TemplateError:
                If the template is not found or unidentifiable.
            BrandError:
                If the referenced brand cannot be loaded.
            ValidationError:
                If the template data violates the template contract.
        """

        index = self._build_index()

        path = index.get(template_id)

        if path is None:
            raise TemplateError(
                f"Template '{template_id}' not found in "
                f"{self.template_dir}."
            )

        data = read_json(path, TemplateError)

        try:
            template = Template.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(
                f"Template '{template_id}' is invalid.",
                format_validation_errors(exc),
            ) from exc

        if template.brand is not None:
            template.brand_profile = self.brand_loader.load(
                template.brand
            )

        return template

    def load_all(self) -> dict[str, Template]:
        """
        Load every discoverable template keyed by id.

        Raises on the first invalid template so broken templates fail
        immediately.
        """

        return {
            template_id: self.load(template_id)
            for template_id in self.discover()
        }

    def get_brand(
        self,
        brand_id: str,
    ) -> BrandProfile:
        """
        Return a brand profile by id.

        Delegates to the brand loader so callers can resolve brands
        independently of templates.
        """

        return self.brand_loader.load(brand_id)

    def _build_index(self) -> dict[str, Path]:
        """
        Build (or return the cached) map of template id to file path.
        """

        if self._index is not None:
            return self._index

        if not self.template_dir.is_dir():
            raise TemplateError(
                f"Template directory not found: {self.template_dir}"
            )

        index: dict[str, Path] = {}

        for path in sorted(self.template_dir.rglob("*.json")):

            data = read_json(path, TemplateError)

            template_id = self._extract_template_id(data, path)

            if template_id in index:
                raise TemplateError(
                    f"Duplicate template id '{template_id}' in "
                    f"'{index[template_id]}' and '{path}'."
                )

            index[template_id] = path

        self._index = index

        return index

    @staticmethod
    def _extract_template_id(
        data: dict[str, Any],
        path: Path,
    ) -> str:
        """
        Extract and validate the template id from its JSON data.
        """

        meta = data.get("meta") or {}

        template_id = meta.get("id")

        if not isinstance(template_id, str) or not template_id.strip():
            raise TemplateError(
                f"Template file '{path}' is missing meta.id."
            )

        return template_id
