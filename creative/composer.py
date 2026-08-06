"""
Image Composer.

Low-level raster composition primitives for the Creative Engine.

Responsibilities:
    - Creating a canvas with a solid background.
    - Placing images with cover, contain or stretch fitting.
    - Drawing rectangles, scrim overlays and gradients.

This module performs no text layout or drawing: text belongs to the
Typography Engine. Composer functions are stateless and deterministic.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from creative.exceptions import RenderError


HEX_RGB: dict[str, tuple[int, int, int]] = {}


def _hex_to_rgb(
    value: str,
) -> tuple[int, int, int]:
    """
    Convert a ``#RRGGBB`` hex color to an RGB tuple.
    """

    cached = HEX_RGB.get(value)

    if cached is not None:
        return cached

    value = value.lstrip("#")

    if len(value) != 6:
        raise RenderError(f"Invalid hex color '{value}'.")

    try:
        rgb = (
            int(value[0:2], 16),
            int(value[2:4], 16),
            int(value[4:6], 16),
        )
    except ValueError as exc:
        raise RenderError(
            f"Invalid hex color '#{value}'."
        ) from exc

    HEX_RGB[value] = rgb

    return rgb


def create_canvas(
    width: int,
    height: int,
    background: str = "#FFFFFF",
) -> Image.Image:
    """
    Create a canvas filled with a solid background color.

    Args:
        width:
            Canvas width in pixels.
        height:
            Canvas height in pixels.
        background:
            ``#RRGGBB`` fill color.

    Returns:
        A new RGB image.
    """

    return Image.new("RGB", (width, height), _hex_to_rgb(background))


def place_image(
    canvas: Image.Image,
    source: Path | str | Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    fit: str = "cover",
) -> None:
    """
    Place an image inside a target box using the given fit mode.

    Modes:
        cover:
            Scale to fill the box, cropping overflow, centered.
        contain:
            Scale to fit inside the box, leaving margins, centered.
        stretch:
            Scale to exactly match the box dimensions.

    Args:
        canvas:
            Target canvas to draw on.
        source:
            Image file path or a PIL image.
        x, y:
            Top-left of the target box.
        width, height:
            Size of the target box.
        fit:
            One of ``cover``, ``contain``, ``stretch``.

    Raises:
        RenderError:
            If the source cannot be loaded or fit is unsupported.
    """

    image = _load_image(source)

    if fit == "cover":
        placed = _fit_cover(image, width, height)
        _paste(canvas, placed, x, y, width, height, cover=True)
    elif fit == "contain":
        placed = _fit_contain(image, width, height)
        _paste(canvas, placed, x, y, placed.width, placed.height)
    elif fit == "stretch":
        placed = image.resize((width, height), Image.LANCZOS)
        _paste(canvas, placed, x, y, width, height)
    else:
        raise RenderError(f"Unsupported image fit '{fit}'.")


def _load_image(
    source: Path | str | Image.Image,
) -> Image.Image:
    """
    Load an image from a path or return the given PIL image.
    """

    if isinstance(source, Image.Image):
        return source.convert("RGB")

    try:
        with Image.open(source) as handle:
            return handle.convert("RGB").copy()
    except (OSError, ValueError) as exc:
        raise RenderError(
            f"Cannot load image '{source}': {exc}"
        ) from exc


def _fit_cover(
    image: Image.Image,
    width: int,
    height: int,
) -> Image.Image:
    """
    Scale and center-crop an image to exactly cover the box.
    """

    if width <= 0 or height <= 0:
        raise RenderError("Target box must have positive dimensions.")

    scale = max(width / image.width, height / image.height)

    resized = image.resize(
        (
            max(1, round(image.width * scale)),
            max(1, round(image.height * scale)),
        ),
        Image.LANCZOS,
    )

    left = (resized.width - width) // 2
    top = (resized.height - height) // 2

    return resized.crop(
        (left, top, left + width, top + height)
    )


def _fit_contain(
    image: Image.Image,
    width: int,
    height: int,
) -> Image.Image:
    """
    Scale an image to fit fully inside the box, preserving aspect.
    """

    if width <= 0 or height <= 0:
        raise RenderError("Target box must have positive dimensions.")

    scale = min(width / image.width, height / image.height)

    return image.resize(
        (
            max(1, round(image.width * scale)),
            max(1, round(image.height * scale)),
        ),
        Image.LANCZOS,
    )


def _paste(
    canvas: Image.Image,
    image: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    cover: bool = False,
) -> None:
    """
    Paste an image onto the canvas, optionally centered in the box.
    """

    if cover:
        canvas.paste(image, (x, y))
        return

    offset_x = x + (width - image.width) // 2
    offset_y = y + (height - image.height) // 2

    canvas.paste(image, (offset_x, offset_y))


def draw_rect(
    canvas: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    color: str,
    radius: int = 0,
) -> None:
    """
    Draw a solid rectangle (optionally rounded) onto the canvas.
    """

    draw = ImageDraw.Draw(canvas)

    if radius > 0:
        draw.rounded_rectangle(
            (x, y, x + width, y + height),
            radius=radius,
            fill=_hex_to_rgb(color),
        )
    else:
        draw.rectangle(
            (x, y, x + width, y + height),
            fill=_hex_to_rgb(color),
        )


def draw_overlay(
    canvas: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    color: str = "#000000",
    opacity: float = 0.35,
) -> None:
    """
    Draw a translucent scrim over a region of the canvas.

    Args:
        canvas:
            Target canvas.
        x, y, width, height:
            Region to cover.
        color:
            ``#RRGGBB`` scrim color.
        opacity:
            Scrim opacity from 0.0 (invisible) to 1.0 (opaque).
    """

    opacity = max(0.0, min(1.0, float(opacity)))

    overlay = Image.new(
        "RGBA",
        (width, height),
        (*_hex_to_rgb(color), round(255 * opacity)),
    )

    canvas.paste(
        Image.alpha_composite(
            canvas.crop((x, y, x + width, y + height)).convert("RGBA"),
            overlay,
        ).convert("RGB"),
        (x, y),
    )


def draw_gradient(
    canvas: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    top_color: str,
    bottom_color: str,
) -> None:
    """
    Draw a vertical linear gradient from top to bottom color.
    """

    top = _hex_to_rgb(top_color)
    bottom = _hex_to_rgb(bottom_color)

    gradient = Image.new("RGB", (width, height))

    draw = ImageDraw.Draw(gradient)

    for row in range(height):

        ratio = row / max(1, height - 1)

        color = tuple(
            round(top[i] + (bottom[i] - top[i]) * ratio)
            for i in range(3)
        )

        draw.line([(0, row), (width, row)], fill=color)

    canvas.paste(gradient, (x, y))


def _star_polygon(
    center_x: float,
    center_y: float,
    radius: float,
) -> list[tuple[float, float]]:
    """
    Build a five-pointed star polygon centered on the given point.

    The inner radius is derived so the star has the classic five-point
    silhouette rather than looking like a decagon.
    """

    import math

    inner_radius = radius * 0.382

    points: list[tuple[float, float]] = []

    for index in range(10):

        angle = -math.pi / 2 + index * math.pi / 5

        r = radius if index % 2 == 0 else inner_radius

        points.append(
            (
                center_x + r * math.cos(angle),
                center_y + r * math.sin(angle),
            )
        )

    return points


def draw_stars(
    canvas: Image.Image,
    x: int,
    y: int,
    size: int,
    rating: float,
    color: str,
    max_stars: int = 5,
) -> None:
    """
    Draw a row of star shapes representing a rating value.

    Fully filled stars are drawn for the integer part; a partial star
    is drawn for the fractional remainder. Any remaining stars are
    drawn as outlines so the scale is visible.

    Args:
        canvas:
            Target canvas.
        x, y:
            Top-left of the first star.
        size:
            Star width/height in pixels.
        rating:
            Rating value from 0.0 to ``max_stars``.
        color:
            ``#RRGGBB`` fill color for filled stars.
        max_stars:
            Total number of stars to draw.
    """

    draw = ImageDraw.Draw(canvas)

    rgb = _hex_to_rgb(color)
    outline_rgb = tuple(min(255, channel + 90) for channel in rgb)

    clamped = max(0.0, min(float(max_stars), float(rating)))

    full = int(clamped)
    fraction = clamped - full

    for index in range(max_stars):

        center_x = x + size / 2 + index * size
        center_y = y + size / 2

        polygon = _star_polygon(center_x, center_y, size / 2)

        if index < full:

            draw.polygon(polygon, fill=rgb)
            continue

        if index == full and fraction > 0:

            _draw_partial_star(
                canvas,
                polygon,
                x + index * size,
                y,
                size,
                fraction,
                rgb,
            )
            continue

        draw.polygon(polygon, outline=outline_rgb, width=1)


def _draw_partial_star(
    canvas: Image.Image,
    polygon: list[tuple[float, float]],
    star_x: int,
    star_y: int,
    size: int,
    fraction: float,
    color: tuple[int, int, int],
) -> None:
    """
    Fill the left ``fraction`` of a star with the given color.

    Uses a mask so the partial fill clips cleanly to the star shape.
    """

    mask = Image.new("L", (size, size), 0)

    mask_draw = ImageDraw.Draw(mask)

    shifted = [
        (px - star_x, py - star_y)
        for px, py in polygon
    ]

    mask_draw.polygon(shifted, fill=255)

    clip = Image.new("L", (size, size), 255)

    clip_draw = ImageDraw.Draw(clip)

    clip_draw.rectangle(
        (round(size * fraction), 0, size, size),
        fill=0,
    )

    mask = Image.composite(mask, Image.new("L", (size, size), 0), clip)

    fill = Image.new("RGB", (size, size), color)

    canvas.paste(fill, (star_x, star_y), mask)
