"""
Brand Profile Loader.

Loads and validates brand profiles for the Creative Engine.

Brand profiles are JSON files in the brand directory. Each file is
named ``<brand_id>.json`` and must declare a matching ``id`` field.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError as PydanticValidationError

from creative._io import format_validation_errors, read_json
from creative.exceptions import BrandError, ValidationError
from creative.models import BrandProfile


DEFAULT_BRAND_DIR = Path(__file__).parent / "assets" / "brands"


class BrandProfileLoader:
    """
    Loader for brand profile JSON files.

    Discovers, loads and validates brand profiles from a single
    directory. Loaded profiles are returned as BrandProfile objects.
    """

    def __init__(
        self,
        brand_dir: Path | None = None,
    ) -> None:
        self.brand_dir = brand_dir or DEFAULT_BRAND_DIR

    def discover(self) -> list[str]:
        """
        Return the ids of all brand profiles, sorted.

        Raises:
            BrandError:
                If the brand directory does not exist.
        """

        if not self.brand_dir.is_dir():
            raise BrandError(
                f"Brand directory not found: {self.brand_dir}"
            )

        return sorted(
            path.stem for path in self.brand_dir.glob("*.json")
        )

    def load(
        self,
        brand_id: str,
    ) -> BrandProfile:
        """
        Load and validate a brand profile by id.

        Args:
            brand_id:
                Id of the brand profile (the file stem).

        Raises:
            BrandError:
                If the profile is missing, unreadable, or its id does
                not match the file name.
            ValidationError:
                If the profile data violates the brand schema.
        """

        path = self.brand_dir / f"{brand_id}.json"

        if not path.is_file():
            raise BrandError(
                f"Brand '{brand_id}' not found in {self.brand_dir}."
            )

        data = read_json(path, BrandError)

        try:
            profile = BrandProfile.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(
                f"Brand '{brand_id}' is invalid.",
                format_validation_errors(exc),
            ) from exc

        if profile.id != brand_id:
            raise BrandError(
                f"Brand '{brand_id}' declares id '{profile.id}' "
                f"in '{path.name}'."
            )

        return profile
