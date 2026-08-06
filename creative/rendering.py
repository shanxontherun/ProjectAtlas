"""
Rendering Engine.

Orchestrates the Creative Engine pipeline for a single creative:

    1. Load the template through the registry (brand attached).
    2. Resolve content values via the template's data map.
    3. Build the canvas and per-zone layers.
    4. Invoke the Composer for image/shape layers and the Typography
       Engine for text layers.
    5. Save the finished image to an output directory.

The engine is pure with respect to persistence: it writes image files
only and never touches the database or the worker queue. Rendering is
stateless and deterministic for a given set of inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from creative import composer
from creative.exceptions import RenderError
from creative.models import Bounds, BrandProfile, Template, Zone
from creative.registry import TemplateRegistry
from creative.typography import FontResolver, layout_text


DEFAULT_OUTPUT_DIR = Path(__file__).parent / "generated"

DEFAULT_LINE_SPACING = 1.15
DEFAULT_FIT = "cover"


@dataclass(frozen=True)
class RenderResult:
    """
    Outcome of a render.

    Attributes:
        template_id:
            Id of the template that was rendered.
        variant:
            Output variant used for the filename.
        path:
            Absolute path of the written image file.
        width, height:
            Dimensions of the rendered image.
        output_format:
            File format actually written (``png``, ``jpeg``, ``webp``).
    """

    template_id: str
    variant: str
    path: Path
    width: int
    height: int
    output_format: str


class RenderingEngine:
    """
    High-level renderer for data-driven creative templates.

    Args:
        registry:
            Template registry used to load templates and brands.
        font_resolver:
            Font resolver used by the typography engine.
        output_dir:
            Directory where rendered images are saved. Created on
            demand if it does not exist.
    """

    def __init__(
        self,
        registry: TemplateRegistry | None = None,
        font_resolver: FontResolver | None = None,
        output_dir: Path | None = None,
    ) -> None:
        self.registry = registry or TemplateRegistry()
        self.font_resolver = font_resolver or FontResolver()
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR

    def render(
        self,
        template_id: str,
        content: dict[str, object],
        product_image: Path | str | Image.Image,
        platform: str | None = None,
        output_dir: Path | None = None,
        output_filename: str | None = None,
    ) -> RenderResult:
        """
        Render a template to an image file.

        Args:
            template_id:
                Id of the template to render.
            content:
                Values keyed by data-map target name (e.g.
                ``pinterest_title``, ``rating``, ``cta``).
            product_image:
                Product image used by image zones. Accepts a path or
                a PIL image.
            platform:
                Optional platform name; when given, platform overrides
                on the canvas and zones are applied.
            output_dir:
                Overrides the engine's default output directory for
                this render.

        Raises:
            RenderError:
                If a zone cannot be rendered or the output cannot be
                written.

        Returns:
            RenderResult describing the written file.
        """

        template = self.registry.load(template_id)

        brand = template.brand_profile

        canvas_bounds = self._canvas_bounds(template, platform)

        image = composer.create_canvas(
            canvas_bounds.width,
            canvas_bounds.height,
            template.canvas.background,
        )

        for zone in template.zones:

            self._render_zone(
                image,
                template,
                zone,
                brand,
                content,
                product_image,
                platform,
            )

        return self._save(
            image,
            template,
            output_dir or self.output_dir,
            output_filename,
        )

    # -- zone dispatch -------------------------------------------------

    def _render_zone(
        self,
        image: Image.Image,
        template: Template,
        zone: Zone,
        brand: BrandProfile | None,
        content: dict[str, object],
        product_image: Path | str | Image.Image,
        platform: str | None,
    ) -> None:
        """
        Dispatch a single zone to its renderer.
        """

        bounds = self._zone_bounds(zone, platform)

        if not self._zone_is_visible(zone, content):
            return

        data_map = template.data_map

        if zone.type == "image":
            self._render_image_zone(image, bounds, zone, product_image)
        elif zone.type in ("text", "price", "badge"):
            self._render_text_zone(
                image, bounds, zone, brand, content, data_map
            )
        elif zone.type == "rating":
            self._render_rating_zone(
                image, bounds, zone, brand, content, data_map
            )
        elif zone.type == "watermark":
            self._render_watermark(image, bounds, zone, brand)
        elif zone.type == "logo":
            self._render_logo(image, bounds, zone, brand)
        elif zone.type == "rect":
            self._render_rect(image, bounds, zone, brand)
        elif zone.type == "overlay":
            self._render_overlay(image, bounds, zone, brand)
        elif zone.type == "gradient":
            self._render_gradient(image, bounds, zone, brand)
        else:
            raise RenderError(
                f"Zone '{zone.name}' has unsupported type "
                f"'{zone.type}'."
            )

    # -- individual zone renderers --------------------------------------

    def _render_image_zone(
        self,
        image: Image.Image,
        bounds: Bounds,
        zone: Zone,
        product_image: Path | str | Image.Image,
    ) -> None:
        """
        Place the product image into an image zone.
        """

        fit = str(zone.style.get("fit", DEFAULT_FIT))

        composer.place_image(
            image,
            product_image,
            bounds.x,
            bounds.y,
            bounds.width,
            bounds.height,
            fit=fit,
        )

    def _render_text_zone(
        self,
        image: Image.Image,
        bounds: Bounds,
        zone: Zone,
        brand: BrandProfile | None,
        content: dict[str, object],
        data_map: dict[str, str],
    ) -> None:
        """
        Lay out and draw a text zone (text, price, badge).
        """

        text = self._content_value(zone, content, data_map)

        if not isinstance(text, str) or not text.strip():
            raise RenderError(
                f"Zone '{zone.name}' requires non-empty text content."
            )

        layout = layout_text(
            self.font_resolver,
            self._font_name(zone, brand),
            text,
            bounds.x,
            bounds.y,
            bounds.width,
            bounds.height,
            font_size=self._font_size(zone),
            align=str(zone.style.get("align", "left")),
            valign=str(zone.style.get("valign", "top")),
            line_spacing=float(
                zone.style.get("line_spacing", DEFAULT_LINE_SPACING)
            ),
        )

        self._draw_text(image, layout, self._color(zone, brand))

    def _render_rating_zone(
        self,
        image: Image.Image,
        bounds: Bounds,
        zone: Zone,
        brand: BrandProfile | None,
        content: dict[str, object],
        data_map: dict[str, str],
    ) -> None:
        """
        Draw star shapes plus the numeric rating value.
        """

        value = self._content_value(zone, content, data_map)

        try:
            rating = float(value)
        except (TypeError, ValueError) as exc:
            raise RenderError(
                f"Zone '{zone.name}' requires a numeric rating, "
                f"got '{value}'."
            ) from exc

        color = self._color(zone, brand)

        star_size = bounds.height

        composer.draw_stars(
            image,
            bounds.x,
            bounds.y,
            star_size,
            rating,
            color,
        )

        number_layout = layout_text(
            self.font_resolver,
            self._font_name(zone, brand),
            f"{rating:.1f}",
            bounds.x + star_size * 5 + 16,
            bounds.y,
            max(1, bounds.width - star_size * 5 - 16),
            bounds.height,
            font_size=None,
            align="left",
            valign="middle",
        )

        self._draw_text(image, number_layout, color)

    def _render_watermark(
        self,
        image: Image.Image,
        bounds: Bounds,
        zone: Zone,
        brand: BrandProfile | None,
    ) -> None:
        """
        Draw the brand watermark text into the watermark zone.
        """

        watermark = (brand.watermark if brand else {}) or {}

        text = zone.style.get("text")

        if text is None:
            text = watermark.get("text")

        if not isinstance(text, str) or not text.strip():
            return

        align = {
            "bottom-right": "right",
            "bottom-left": "left",
            "bottom-center": "center",
        }.get(
            str(watermark.get("position", "bottom-right")),
            "right",
        )

        layout = layout_text(
            self.font_resolver,
            self._font_name(zone, brand),
            text,
            bounds.x,
            bounds.y,
            bounds.width,
            bounds.height,
            font_size=self._font_size(zone) or 20,
            align=align,
            valign="bottom",
            line_spacing=DEFAULT_LINE_SPACING,
        )

        color = zone.style.get("color")

        if color is None:
            color = watermark.get("color", "#999999")

        self._draw_text(image, layout, str(color))

    def _render_logo(
        self,
        image: Image.Image,
        bounds: Bounds,
        zone: Zone,
        brand: BrandProfile | None,
    ) -> None:
        """
        Place the brand logo into a logo zone.
        """

        logo = (brand.logo if brand else None)

        if not logo:
            raise RenderError(
                f"Zone '{zone.name}' requires a brand logo, but "
                f"brand '{brand.id if brand else '?'}' has none."
            )

        logo_path = self._resolve_asset_path(logo)

        fit = str(zone.style.get("fit", "contain"))

        composer.place_image(
            image,
            logo_path,
            bounds.x,
            bounds.y,
            bounds.width,
            bounds.height,
            fit=fit,
        )

    def _render_rect(
        self,
        image: Image.Image,
        bounds: Bounds,
        zone: Zone,
        brand: BrandProfile | None,
    ) -> None:
        """
        Draw a solid rectangle zone.
        """

        composer.draw_rect(
            image,
            bounds.x,
            bounds.y,
            bounds.width,
            bounds.height,
            color=self._color(zone, brand),
            radius=int(zone.style.get("radius", 0)),
        )

    def _render_overlay(
        self,
        image: Image.Image,
        bounds: Bounds,
        zone: Zone,
        brand: BrandProfile | None,
    ) -> None:
        """
        Draw a scrim overlay zone, defaulting to brand overlay values.
        """

        overlays = (brand.overlays if brand else {}) or {}

        color = str(
            zone.style.get(
                "color",
                overlays.get("scrim_color", "#000000"),
            )
        )

        opacity = float(
            zone.style.get(
                "opacity",
                overlays.get("scrim_opacity", 0.35),
            )
        )

        composer.draw_overlay(
            image,
            bounds.x,
            bounds.y,
            bounds.width,
            bounds.height,
            color=color,
            opacity=opacity,
        )

    def _render_gradient(
        self,
        image: Image.Image,
        bounds: Bounds,
        zone: Zone,
        brand: BrandProfile | None,
    ) -> None:
        """
        Draw a vertical gradient zone.
        """

        top_color = self._color(zone, brand)

        bottom_color = str(
            zone.style.get(
                "bottom_color",
                top_color,
            )
        )

        composer.draw_gradient(
            image,
            bounds.x,
            bounds.y,
            bounds.width,
            bounds.height,
            top_color=top_color,
            bottom_color=bottom_color,
        )

    # -- style resolution helpers ----------------------------------------

    def _font_name(
        self,
        zone: Zone,
        brand: BrandProfile | None,
    ) -> str:
        """
        Resolve a zone's font role to a concrete font name.
        """

        explicit = zone.style.get("font")

        if explicit:
            return str(explicit)

        role = zone.style.get("font_role", "body")

        if brand is not None:

            font = brand.fonts.get(str(role))

            if font:
                return font

        raise RenderError(
            f"Zone '{zone.name}' references unknown font role "
            f"'{role}'."
        )

    def _font_size(
        self,
        zone: Zone,
    ) -> int | None:
        """
        Return the explicit font size, if any.
        """

        size = zone.style.get("font_size")

        if size is None:
            return None

        return max(1, int(size))

    def _color(
        self,
        zone: Zone,
        brand: BrandProfile | None,
    ) -> str:
        """
        Resolve a zone's color from an explicit value or palette role.
        """

        explicit = zone.style.get("color")

        if explicit:
            return str(explicit)

        role = zone.style.get("color_role", "text")

        if brand is not None:

            palette_color = brand.palette.get(str(role))

            if palette_color:
                return palette_color

        raise RenderError(
            f"Zone '{zone.name}' references unknown color role "
            f"'{role}'."
        )

    # -- content and bounds helpers ---------------------------------------

    def _content_value(
        self,
        zone: Zone,
        content: dict[str, object],
        data_map: dict[str, str],
    ) -> object:
        """
        Resolve a zone's content value via the template data map.

        Zones without a data-map entry look themselves up directly.
        """

        key = data_map.get(zone.name, zone.name)

        return content.get(key)

    def _zone_is_visible(
        self,
        zone: Zone,
        content: dict[str, object],
    ) -> bool:
        """
        Honor ``visible_if``: hide the zone when the referenced
        content key is falsy.
        """

        if not zone.visible_if:
            return True

        return bool(content.get(zone.visible_if))

    def _zone_bounds(
        self,
        zone: Zone,
        platform: str | None,
    ) -> Bounds:
        """
        Return a zone's bounds, applying platform overrides if present.
        """

        if platform is not None:

            override = zone.platform_overrides.get(platform)

            if override is not None:
                return override

        return zone.bounds

    def _canvas_bounds(
        self,
        template: Template,
        platform: str | None,
    ) -> Bounds:
        """
        Return the effective canvas size for a template/platform.
        """

        if platform is not None:

            override = template.canvas.platform_overrides.get(platform)

            if isinstance(override, dict):

                width = int(override.get("width", template.canvas.width))
                height = int(override.get("height", template.canvas.height))

                return Bounds(x=0, y=0, width=width, height=height)

        return Bounds(
            x=0,
            y=0,
            width=template.canvas.width,
            height=template.canvas.height,
        )

    def _resolve_asset_path(
        self,
        asset: str,
    ) -> Path:
        """
        Resolve a brand-relative asset to an absolute path.

        Asset paths are relative to the assets root (the parent of
        the brand directory), e.g. ``logos/atlas.png``.
        """

        path = Path(asset)

        if path.is_absolute():
            return path

        assets_dir = self.registry.brand_loader.brand_dir.parent

        candidate = assets_dir / asset

        if not candidate.is_file():
            raise RenderError(
                f"Brand asset '{asset}' not found near {assets_dir}."
            )

        return candidate

    def _draw_text(
        self,
        image: Image.Image,
        layout,
        color: str,
    ) -> None:
        """
        Draw every line of a text layout onto the image.

        The top-left of each line is placed exactly at the layout's
        measured box origin by compensating for the font's ink offset.
        """

        draw = ImageDraw.Draw(image)

        for line in layout.lines:

            bbox = layout.font.getbbox(line.text)

            draw.text(
                (line.x - bbox[0], line.y - bbox[1]),
                line.text,
                font=layout.font,
                fill=color,
            )

    def _save(
        self,
        image: Image.Image,
        template: Template,
        output_dir: Path,
        output_filename: str | None = None,
    ) -> RenderResult:
        """
        Write the rendered image to the output directory.
        """

        output = template.output


        if output_filename is None:
            filename = output.filename_pattern.format(
                template_id=template.meta.id,
                variant=output.variant,
            )
        else:
            filename = output_filename

        extension = {
            "png": "png",
            "jpeg": "jpg",
            "webp": "webp",
        }.get(output.format, "png")

        path = output_dir / f"{filename}.{extension}"

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            save_kwargs: dict[str, object] = {}

            if output.format == "jpeg":
                save_kwargs["quality"] = output.quality
                save_kwargs["optimize"] = True
            elif output.format == "webp":
                save_kwargs["quality"] = output.quality

            image.save(path, format=output.format.upper(), **save_kwargs)
        except OSError as exc:
            raise RenderError(
                f"Cannot write rendered image to '{path}': {exc}"
            ) from exc

        return RenderResult(
            template_id=template.meta.id,
            variant=output.variant,
            path=path,
            width=image.width,
            height=image.height,
            output_format=output.format,
        )
