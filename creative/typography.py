"""
Typography Engine.

Pure text layout and measurement for the Creative Engine.

Responsibilities:
    - Resolving font roles (e.g. ``title``, ``body``) to concrete
      fonts, with a deterministic fallback chain.
    - Wrapping text to a maximum width.
    - Measuring single and multi-line text.
    - Computing line positions for a given alignment and line spacing.
    - Auto-fitting font size to a target bounding box.

This module performs no composition: it never draws onto an image.
Callers consume the returned layout to draw text themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont

from creative.exceptions import RenderError


DEFAULT_FONT_DIR = Path(__file__).parent / "assets" / "fonts"

# Fallback sizes for the bundled default font when no real font
# files are available.
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 400
AUTO_FIT_STEP = 2


@dataclass(frozen=True)
class FontRole:
    """
    A resolved font at a fixed pixel size.

    Attributes:
        name:
            The logical font role (e.g. ``title``) this was resolved
            from, for error reporting.
        pil_font:
            The concrete Pillow font to draw with.
        size:
            The resolved pixel size.
    """

    name: str
    pil_font: ImageFont.FreeTypeFont
    size: int


@dataclass(frozen=True)
class TextLine:
    """
    A single laid-out line of text.

    Attributes:
        text:
            The line content, already wrapped.
        x, y:
            Top-left anchor of the line's measured box.
        width, height:
            Measured size of the line in pixels.
    """

    text: str
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class TextLayout:
    """
    Result of laying out a block of text.

    Attributes:
        lines:
            The laid-out lines in top-to-bottom order.
        font:
            The font used for every line.
        size:
            The (possibly auto-fit) font size used.
    """

    lines: list[TextLine]
    font: ImageFont.FreeTypeFont
    size: int

    @property
    def width(self) -> int:
        """
        Widest line width in pixels.
        """

        return max((line.width for line in self.lines), default=0)

    @property
    def height(self) -> int:
        """
        Total stacked height of all lines in pixels.
        """

        return sum(line.height for line in self.lines)


class FontResolver:
    """
    Resolves font roles to concrete fonts.

    Font names reference either a bundled font file (looked up in a
    search directory, matching by stem) or the Pillow default font as
    a final fallback. Resolution is deterministic: the first existing
    file wins, otherwise the default font is used.
    """

    def __init__(
        self,
        search_dirs: list[Path] | None = None,
    ) -> None:
        self.search_dirs = search_dirs or [DEFAULT_FONT_DIR]
        self._cache: dict[tuple[str, int], FontRole] = {}

    def resolve(
        self,
        font_name: str,
        size: int,
    ) -> FontRole:
        """
        Resolve a font name at the given pixel size.

        Args:
            font_name:
                Logical font name or role to resolve.
            size:
                Desired pixel size, clamped to the supported range.

        Raises:
            RenderError:
                If the name is empty.
        """

        size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, int(size)))

        cache_key = (font_name, size)

        if cache_key not in self._cache:
            self._cache[cache_key] = self._load(font_name, size)

        return self._cache[cache_key]

    def _load(
        self,
        font_name: str,
        size: int,
    ) -> FontRole:
        """
        Load the best available font for the given name and size.
        """

        if not font_name:
            raise RenderError("Font name must not be empty.")

        path = self._find_font_file(font_name)

        if path is not None:
            try:
                pil_font = ImageFont.truetype(str(path), size=size)
            except OSError as exc:
                raise RenderError(
                    f"Cannot load font file '{path}': {exc}"
                ) from exc
        else:
            pil_font = ImageFont.load_default(size=size)

        return FontRole(
            name=font_name,
            pil_font=pil_font,
            size=size,
        )

    def _find_font_file(
        self,
        font_name: str,
    ) -> Path | None:
        """
        Locate a font file by stem across the search directories.
        """

        for directory in self.search_dirs:

            if not directory.is_dir():
                continue

            for pattern in (
                f"{font_name}.ttf",
                f"{font_name}.otf",
                f"{font_name}.TTF",
                f"{font_name}.OTF",
            ):
                candidate = directory / pattern

                if candidate.is_file():
                    return candidate

        return None


def measure(
    font: ImageFont.FreeTypeFont,
    text: str,
) -> tuple[int, int]:
    """
    Measure a single line of text.

    Args:
        font:
            Font to measure with.
        text:
            Text to measure.

    Returns:
        Tuple of (width, height) in pixels.
    """

    bbox = font.getbbox(text)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]

    return width, height


def wrap_text(
    font: ImageFont.FreeTypeFont,
    text: str,
    max_width: int,
) -> list[str]:
    """
    Greedy word-wrap text to the given maximum width.

    Words that alone exceed the maximum width are split on character
    boundaries so no line ever overflows.

    Args:
        font:
            Font used to measure line widths.
        text:
            Text to wrap. Internal newlines are honored.
        max_width:
            Maximum line width in pixels.

    Returns:
        List of wrapped lines.
    """

    if not text:
        return []

    wrapped: list[str] = []

    for paragraph in text.split("\n"):

        if not paragraph:
            wrapped.append("")
            continue

        line = ""

        for word in paragraph.split():

            candidate = f"{line} {word}".strip()

            if measure(font, candidate)[0] <= max_width:
                line = candidate
                continue

            if line:
                wrapped.append(line)
                line = ""

            line = _wrap_oversized_word(font, word, max_width, wrapped)

        if line:
            wrapped.append(line)

    return wrapped


def _wrap_oversized_word(
    font: ImageFont.FreeTypeFont,
    word: str,
    max_width: int,
    wrapped: list[str],
) -> str:
    """
    Split a word wider than the maximum width across lines.

    Returns the remaining partial line and appends full chunks to
    ``wrapped``.
    """

    remainder = word

    while remainder:

        if measure(font, remainder)[0] <= max_width:
            return remainder

        chunk = ""

        for char in remainder:

            candidate = chunk + char

            if measure(font, candidate)[0] > max_width:
                break

            chunk = candidate

        if not chunk:
            chunk = remainder[0]
            remainder = remainder[1:]
        else:
            remainder = remainder[len(chunk):]

        if remainder:
            wrapped.append(chunk)
        else:
            return chunk

    return ""


def fit_font_size(
    resolver: FontResolver,
    font_name: str,
    text: str,
    max_width: int,
    max_height: int,
    preferred_size: int,
) -> tuple[ImageFont.FreeTypeFont, int]:
    """
    Find the largest font size whose wrapped layout fits the box.

    The algorithm starts from the preferred size and steps down until
    the wrapped text fits both dimensions. When text never fits, the
    minimum supported size is returned rather than failing.

    Args:
        resolver:
            Font resolver used to build candidate fonts.
        font_name:
            Font name or role to resolve candidates from.
        text:
            Text to fit.
        max_width:
            Maximum layout width in pixels.
        max_height:
            Maximum layout height in pixels.
        preferred_size:
            Starting font size to try.

    Returns:
        Tuple of (font, size) that fits the box.
    """

    size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, int(preferred_size)))

    while size > MIN_FONT_SIZE:

        font = resolver.resolve(font_name, size).pil_font

        lines = wrap_text(font, text, max_width)
        total_height = sum(measure(font, line)[1] for line in lines)

        if total_height <= max_height:
            return font, size

        size -= AUTO_FIT_STEP

    font = resolver.resolve(font_name, MIN_FONT_SIZE).pil_font

    return font, MIN_FONT_SIZE


def layout_text(
    resolver: FontResolver,
    font_name: str,
    text: str,
    x: int,
    y: int,
    width: int,
    height: int,
    font_size: int | None,
    align: str = "left",
    valign: str = "top",
    line_spacing: float = 1.0,
) -> TextLayout:
    """
    Lay out a block of text inside a bounding box.

    Handles wrapping, alignment, vertical alignment, line spacing and
    (when ``font_size`` is None) automatic font sizing. Produces only
    positions: it does not draw.

    Args:
        resolver:
            Font resolver for font lookup and auto-fit.
        font_name:
            Font name or role to use.
        text:
            Text to lay out.
        x, y:
            Top-left of the target bounding box.
        width, height:
            Size of the target bounding box.
        font_size:
            Fixed font size, or None to auto-fit to the box.
        align:
            Horizontal alignment: ``left``, ``center`` or ``right``.
        valign:
            Vertical alignment: ``top``, ``middle`` or ``bottom``.
        line_spacing:
            Multiplier applied to each line's measured height.

    Raises:
        RenderError:
            If the font cannot be resolved or alignment is invalid.
    """

    if align not in ("left", "center", "right"):
        raise RenderError(
            f"Unsupported horizontal alignment '{align}'."
        )

    if valign not in ("top", "middle", "bottom"):
        raise RenderError(
            f"Unsupported vertical alignment '{valign}'."
        )

    if not text:
        font = resolver.resolve(font_name, font_size or 14).pil_font

        return TextLayout(lines=[], font=font, size=font_size or 14)

    if font_size is None:
        font, size = fit_font_size(
            resolver,
            font_name,
            text,
            width,
            height,
            preferred_size=height,
        )
    else:
        font = resolver.resolve(font_name, font_size).pil_font
        size = font_size

    raw_lines = wrap_text(font, text, width)

    laid_lines: list[TextLine] = []
    cursor_y = y

    for line in raw_lines:

        line_width, line_height = measure(font, line)

        if align == "center":
            line_x = x + (width - line_width) // 2
        elif align == "right":
            line_x = x + width - line_width
        else:
            line_x = x

        laid_lines.append(
            TextLine(
                text=line,
                x=line_x,
                y=cursor_y,
                width=line_width,
                height=line_height,
            )
        )

        cursor_y += round(line_height * line_spacing)

    total_height = sum(line.height for line in laid_lines)
    offset = max(0, height - total_height)

    if valign == "middle":
        offset //= 2
    elif valign == "top":
        offset = 0

    if offset and laid_lines:
        laid_lines = [
            TextLine(
                text=line.text,
                x=line.x,
                y=line.y + offset,
                width=line.width,
                height=line.height,
            )
            for line in laid_lines
        ]

    return TextLayout(lines=laid_lines, font=font, size=size)
