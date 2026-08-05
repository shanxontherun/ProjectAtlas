"""
Pinterest Client.

Handles all communication with Pinterest.
"""

from __future__ import annotations

from typing import Any


def publish_pin(
    *,
    title: str,
    description: str,
    image_url: str,
    affiliate_url: str,
    board_name: str,
) -> bool:
    """
    Publish a Pinterest pin.

    Returns:
        True if publishing succeeds.
        False otherwise.
    """

    print("=" * 60)
    print("PINTEREST CLIENT")
    print("=" * 60)

    print(f"Board       : {board_name}")
    print(f"Title       : {title}")
    print(f"Description : {description}")
    print(f"Image       : {image_url}")
    print(f"Affiliate   : {affiliate_url}")

    print()
    print("Publishing simulation successful.")
    print("=" * 60)

    return True
    