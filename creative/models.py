"""
Creative Engine data models.

Pydantic contracts for the data-driven JSON templates and brand
profiles consumed by the Creative Engine. These models are pure data
contracts: they hold no rendering or I/O logic.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


# Zone types renderable by the engine. Extending this set is the
# only change needed to add a new kind of composable layer.
ZoneType = Literal[
    "image",
    "text",
    "rect",
    "badge",
    "rating",
    "price",
    "logo",
    "overlay",
    "gradient",
    "watermark",
]


class Bounds(BaseModel):
    """
    Position and size of a zone on the canvas.

    Coordinates are absolute pixel values. Percentage and anchor
    based layout is a Phase B concern and belongs to the layout
    engine, not the template contract.
    """

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)

    def fits_within(
        self,
        canvas_width: int,
        canvas_height: int,
    ) -> bool:
        """
        Return True if these bounds stay inside the given canvas.
        """

        return (
            self.x + self.width <= canvas_width
            and self.y + self.height <= canvas_height
        )


class Zone(BaseModel):
    """
    A single composable layer in a template.

    ``style`` carries renderer-specific presentation values (font
    role, color role, alignment, etc.) as free-form data; renderers
    interpret it in Phase B.
    """

    name: str = Field(min_length=1)
    type: ZoneType
    bounds: Bounds
    style: dict[str, Any] = Field(default_factory=dict)
    platform_overrides: dict[str, Bounds] = Field(default_factory=dict)
    visible_if: str | None = None


class Canvas(BaseModel):
    """
    Canvas size and background for a template.
    """

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    background: str = Field(default="#FFFFFF")
    platform_overrides: dict[str, Any] = Field(default_factory=dict)

    @field_validator("background")
    @classmethod
    def background_must_be_hex(
        cls,
        value: str,
    ) -> str:
        """
        Require a valid hex color for the background.
        """

        if not HEX_COLOR_PATTERN.fullmatch(value):
            raise ValueError(
                f"background must be a hex color like '#FFFFFF', got '{value}'"
            )

        return value


class TemplateMeta(BaseModel):
    """
    Identifying metadata for a template.
    """

    id: str = Field(min_length=1)
    version: str = Field(default="1.0.0", min_length=1)
    platforms: list[str] = Field(default_factory=list)
    description: str = ""


class OutputConfig(BaseModel):
    """
    Output configuration for a rendered template.
    """

    filename_pattern: str = Field(default="{template_id}_{variant}")
    format: Literal["png", "jpeg", "webp"] = "png"
    quality: int = Field(default=95, ge=1, le=100)
    variant: str = Field(default="default", min_length=1)


class BrandProfile(BaseModel):
    """
    Reusable visual identity referenced by templates.

    Templates reference brands by id instead of hardcoding styling,
    so one template can render under many brands.
    """

    id: str = Field(min_length=1)
    name: str = ""
    palette: dict[str, str] = Field(default_factory=dict)
    fonts: dict[str, str] = Field(default_factory=dict)
    logo: str | None = None
    watermark: dict[str, Any] = Field(default_factory=dict)
    overlays: dict[str, Any] = Field(default_factory=dict)

    @field_validator("palette")
    @classmethod
    def palette_colors_must_be_hex(
        cls,
        value: dict[str, str],
    ) -> dict[str, str]:
        """
        Require every palette entry to be a hex color.
        """

        for name, color in value.items():

            if not HEX_COLOR_PATTERN.fullmatch(color):
                raise ValueError(
                    f"palette.{name} must be a hex color like '#FFFFFF', "
                    f"got '{color}'"
                )

        return value

    @field_validator("fonts")
    @classmethod
    def font_roles_must_be_non_empty(
        cls,
        value: dict[str, str],
    ) -> dict[str, str]:
        """
        Require every font role to resolve to a non-empty font name.
        """

        for role, font in value.items():

            if not font.strip():
                raise ValueError(f"fonts.{role} must not be empty")

        return value


class Template(BaseModel):
    """
    Data-driven creative template.

    ``brand_profile`` is populated by the registry at load time from
    the ``brand`` reference; it is not authored in the template file.
    """

    meta: TemplateMeta
    canvas: Canvas
    zones: list[Zone] = Field(min_length=1)
    data_map: dict[str, str] = Field(default_factory=dict)
    brand: str | None = Field(default=None, min_length=1)
    brand_profile: BrandProfile | None = None
    output: OutputConfig = Field(default_factory=OutputConfig)

    @model_validator(mode="after")
    def zone_names_must_be_unique(
        self,
    ) -> "Template":
        """
        Reject duplicate zone names within a template.
        """

        names = [zone.name for zone in self.zones]

        duplicates = sorted(
            {name for name in names if names.count(name) > 1}
        )

        if duplicates:
            raise ValueError(
                f"Duplicate zone names: {', '.join(duplicates)}"
            )

        return self

    @model_validator(mode="after")
    def zones_must_fit_canvas(
        self,
    ) -> "Template":
        """
        Reject zones (and their platform overrides) that exceed the
        canvas.
        """

        for zone in self.zones:

            if not zone.bounds.fits_within(
                self.canvas.width,
                self.canvas.height,
            ):
                raise ValueError(
                    f"Zone '{zone.name}' bounds {zone.bounds} exceed "
                    f"canvas {self.canvas.width}x{self.canvas.height}"
                )

            for platform, override in zone.platform_overrides.items():

                if not override.fits_within(
                    self.canvas.width,
                    self.canvas.height,
                ):
                    raise ValueError(
                        f"Zone '{zone.name}' {platform} override "
                        f"{override} exceeds canvas "
                        f"{self.canvas.width}x{self.canvas.height}"
                    )

        return self
