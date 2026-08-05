"""
AI Content validation rules.

Returns validation results for AI-generated content.
"""

from __future__ import annotations

from typing import Any

from services.config import (
    SEO_TITLE_MIN_LENGTH,
    PINTEREST_TITLE_MIN_LENGTH,
    PINTEREST_TITLE_MAX_LENGTH,
    PINTEREST_DESCRIPTION_MIN_LENGTH,
    PINTEREST_DESCRIPTION_MAX_LENGTH,
    MIN_KEYWORDS,
    INSTAGRAM_CAPTION_MIN_LENGTH,
    BLOG_SUMMARY_MIN_LENGTH,
)


def validate_ai_content(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate an AI content record.

    Returns:
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str],
        }
    """

    errors: list[str] = []
    warnings: list[str] = []

    seo_title = (record.get("seo_title") or "").strip()
    pinterest_title = (record.get("pinterest_title") or "").strip()
    pinterest_description = (
        record.get("pinterest_description") or ""
    ).strip()
    pinterest_keywords = (
        record.get("pinterest_keywords") or ""
    ).strip()
    instagram_caption = (
        record.get("instagram_caption") or ""
    ).strip()
    blog_summary = (
        record.get("blog_summary") or ""
    ).strip()

    # --------------------------------------------------
    # Placeholder Values
    # --------------------------------------------------

    invalid_values = {
        "",
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "test",
        "na",
        "n/a",
        "-",
    }

    if seo_title.lower() in invalid_values:
        errors.append("SEO title contains placeholder text.")

    if pinterest_title.lower() in invalid_values:
        errors.append("Pinterest title contains placeholder text.")

    if pinterest_description.lower() in invalid_values:
        errors.append("Pinterest description contains placeholder text.")

    if instagram_caption.lower() in invalid_values:
        errors.append("Instagram caption contains placeholder text.")

    if blog_summary.lower() in invalid_values:
        errors.append("Blog summary contains placeholder text.")

    # --------------------------------------------------
    # SEO Title
    # --------------------------------------------------

    if len(seo_title) < SEO_TITLE_MIN_LENGTH:
        errors.append(
            f"SEO title must be at least {SEO_TITLE_MIN_LENGTH} characters."
        )

    # --------------------------------------------------
    # Pinterest Title
    # --------------------------------------------------

    if len(pinterest_title) < PINTEREST_TITLE_MIN_LENGTH:
        errors.append(
            f"Pinterest title must be at least {PINTEREST_TITLE_MIN_LENGTH} characters."
        )

    elif len(pinterest_title) > PINTEREST_TITLE_MAX_LENGTH:
        errors.append(
            f"Pinterest title cannot exceed {PINTEREST_TITLE_MAX_LENGTH} characters."
        )

    # --------------------------------------------------
    # Pinterest Description
    # --------------------------------------------------

    if len(pinterest_description) < PINTEREST_DESCRIPTION_MIN_LENGTH:
        warnings.append(
            f"Pinterest description is shorter than {PINTEREST_DESCRIPTION_MIN_LENGTH} characters."
        )

    elif len(pinterest_description) > PINTEREST_DESCRIPTION_MAX_LENGTH:
        errors.append(
            f"Pinterest description cannot exceed {PINTEREST_DESCRIPTION_MAX_LENGTH} characters."
        )

    # --------------------------------------------------
    # Pinterest Keywords
    # --------------------------------------------------

    keyword_list = [
        keyword.strip()
        for keyword in pinterest_keywords.split(",")
        if keyword.strip()
    ]

    if len(keyword_list) < MIN_KEYWORDS:
        warnings.append(
            f"Recommended minimum of {MIN_KEYWORDS} Pinterest keywords."
        )

    # --------------------------------------------------
    # Instagram Caption
    # --------------------------------------------------

    if len(instagram_caption) < INSTAGRAM_CAPTION_MIN_LENGTH:
        warnings.append(
            f"Instagram caption is shorter than {INSTAGRAM_CAPTION_MIN_LENGTH} characters."
        )

    # --------------------------------------------------
    # Blog Summary
    # --------------------------------------------------

    if len(blog_summary) < BLOG_SUMMARY_MIN_LENGTH:
        warnings.append(
            f"Blog summary is shorter than {BLOG_SUMMARY_MIN_LENGTH} characters."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }