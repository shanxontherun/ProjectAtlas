"""
HOME_01 Pinterest Template.

Creates a simple Pinterest pin.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


WIDTH = 1000
HEIGHT = 1500

BACKGROUND = (255, 255, 255)

TEXT = (33, 33, 33)

BADGE = (230, 230, 230)


def generate(
    product_image: str,
    headline: str,
    rating: float,
    output_path: str,
) -> None:
    """
    Generate a Pinterest pin.
    """

    canvas = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(canvas)

    try:

        title_font = ImageFont.truetype(
            "arial.ttf",
            56,
        )

        badge_font = ImageFont.truetype(
            "arial.ttf",
            34,
        )

    except OSError:

        title_font = ImageFont.load_default()

        badge_font = ImageFont.load_default()

    image = Image.open(
        product_image,
    ).convert("RGB")

    image.thumbnail(
        (
            800,
            800,
        )
    )

    image_x = (WIDTH - image.width) // 2

    canvas.paste(
        image,
        (
            image_x,
            280,
        ),
    )

    draw.text(
        (
            80,
            80,
        ),
        headline,
        fill=TEXT,
        font=title_font,
    )

    badge = f"★★★★★ {rating:.1f}"

    draw.rounded_rectangle(
        (
            80,
            1120,
            350,
            1185,
        ),
        radius=15,
        fill=BADGE,
    )

    draw.text(
        (
            100,
            1135,
        ),
        badge,
        fill=TEXT,
        font=badge_font,
    )

    draw.text(
        (
            80,
            1270,
        ),
        "Save This Idea",
        fill=TEXT,
        font=badge_font,
    )

    Path(output_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    canvas.save(
        output_path,
        quality=95,
    )