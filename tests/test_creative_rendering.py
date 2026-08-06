"""
Creative Engine Phase B smoke test: Typography, Composer, Renderer.

Renders the data-driven templates through the RenderingEngine and
asserts the outcome is a deterministic, correctly-sized image with
the expected zone content visible.

Run with:  python tests/test_creative_rendering.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image  # noqa: E402

from creative.exceptions import CreativeError, RenderError  # noqa: E402
from creative.rendering import RenderingEngine  # noqa: E402
from creative.registry import TemplateRegistry  # noqa: E402


SAMPLE_CONTENT = {
    "pinterest_title": "Modern kitchen knives set",
    "pinterest_description": "16 piece stainless steel set",
    "rating": 4.8,
    "price": "$49.99",
    "cta": "Shop now",
}

PRODUCT_IMAGE = PROJECT_ROOT / "creative" / "assets" / "test.jpg"


def main() -> None:
    failures: list[str] = []

    def check(
        name: str,
        condition: bool,
        detail: str = "",
    ) -> None:
        status = "ok" if condition else "FAIL"

        print(f"[{status}] {name}")

        if not condition:
            failures.append(f"{name}: {detail}")

    engine = RenderingEngine()

    # Registry discovers both templates.
    templates = TemplateRegistry().discover()
    check(
        "registry discovers templates",
        "home_01" in templates and "home_02" in templates,
        f"discovered {templates}",
    )

    # home_01 renders and is deterministic.
    first = engine.render(
        "home_01",
        dict(SAMPLE_CONTENT),
        product_image=PRODUCT_IMAGE,
    )

    second = engine.render(
        "home_01",
        dict(SAMPLE_CONTENT),
        product_image=PRODUCT_IMAGE,
    )

    first_hash = hashlib.sha256(first.path.read_bytes()).hexdigest()
    second_hash = hashlib.sha256(second.path.read_bytes()).hexdigest()

    check(
        "home_01 output exists",
        first.path.is_file(),
        str(first.path),
    )
    check(
        "home_01 output is 1000x1500",
        (first.width, first.height) == (1000, 1500),
        f"{first.width}x{first.height}",
    )
    check(
        "home_01 output is deterministic",
        first_hash == second_hash,
        f"{first_hash[:12]} != {second_hash[:12]}",
    )

    # home_02 exercises logo, title, subtitle, price and watermark.
    third = engine.render(
        "home_02",
        dict(SAMPLE_CONTENT),
        product_image=PRODUCT_IMAGE,
    )

    third_image = Image.open(third.path).convert("RGB")

    check(
        "home_02 output exists",
        third.path.is_file(),
        str(third.path),
    )
    check(
        "logo zone shows brand primary color",
        third_image.getpixel((160, 90)) == (194, 31, 58),
        f"{third_image.getpixel((160, 90))}",
    )
    check(
        "subtitle zone shows muted color",
        (102, 102, 102)
        in {
            third_image.getpixel((80 + j, y))
            for y in range(285, 335, 2)
            for j in range(0, 840, 20)
        },
        "muted #666666 not found in subtitle region",
    )

    # Error handling: missing text content.
    try:
        engine.render(
            "home_01",
            {"pinterest_title": ""},
            product_image=PRODUCT_IMAGE,
        )
        check("empty text raises RenderError", False, "no exception")
    except RenderError:
        check("empty text raises RenderError", True)

    # Error handling: missing product image file.
    try:
        engine.render(
            "home_01",
            dict(SAMPLE_CONTENT),
            product_image=PROJECT_ROOT / "missing.jpg",
        )
        check("missing image raises RenderError", False, "no exception")
    except RenderError:
        check("missing image raises RenderError", True)

    # Error handling: unknown template.
    try:
        engine.render(
            "does_not_exist",
            dict(SAMPLE_CONTENT),
            product_image=PRODUCT_IMAGE,
        )
        check("unknown template raises CreativeError", False, "no exception")
    except CreativeError:
        check("unknown template raises CreativeError", True)

    print()

    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"  - {failure}")

        sys.exit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
