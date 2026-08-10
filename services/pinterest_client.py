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

    Real Pinterest publishing is not implemented yet (ATLAS-029C only
    makes real Pinterest accounts and boards available to Publishing). To
    avoid fabricating PUBLISHED records for a real account, this raises
    ``NotImplementedError`` instead of simulating success.

    Raises:
        NotImplementedError: Always, until the real publishing sprint.
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
    print("Real Pinterest publishing is not implemented.")
    print("Refusing to fake a publish.")
    print("=" * 60)

    raise NotImplementedError(
        "Real Pinterest publishing isn't implemented yet; "
        "refusing to fake a publish."
    )
    