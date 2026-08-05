"""
Atlas Publisher Worker.

Reads pending queue items and publishes them
using the Pinterest Client.
"""

from __future__ import annotations

from services.queue_service import (
    fetch_next_pending_queue,
    mark_queue_published,
    mark_queue_failed,
)

from services.pinterest_client import publish_pin


def main() -> None:
    """
    Publish the next batch of Pinterest queue items.
    """

    print("=" * 60)
    print("ATLAS PUBLISHER WORKER")
    print("=" * 60)

    queue = fetch_next_pending_queue(limit=10)

    if not queue:
        print("No pending queue items found.")
        return

    print(f"Found {len(queue)} queue item(s).\n")

    for item in queue:

        print("-" * 60)

        print(f"Pin ID              : {item['pin_id']}")
        print(f"Account ID          : {item['account_id']}")
        print(f"Account Name        : {item['account_name']}")
        print(f"Board ID            : {item['board_id']}")
        print(f"Board Name          : {item['board_name']}")

        print()

        print(f"Pinterest Title     : {item['pinterest_title']}")
        print(f"Description         : {item['pinterest_description']}")
        print(f"Keywords            : {item['pinterest_keywords']}")

        print()

        print(f"Affiliate URL       : {item['affiliate_url']}")
        print(f"Image URL           : {item['image_url']}")

        print()

        print(f"Current Status      : {item['status']}")
        print()

        try:

            print("Publishing...\n")

            success = publish_pin(
                title=item["pinterest_title"],
                description=item["pinterest_description"],
                image_url=item["image_url"],
                affiliate_url=item["affiliate_url"],
                board_name=item["board_name"],
            )

            if success:

                mark_queue_published(
                    item["pin_id"]
                )

                print("✓ SUCCESS")
                print()

            else:

                mark_queue_failed(
                    item["pin_id"],
                    "Publishing returned False.",
                )

                print("✗ FAILED")
                print()

        except Exception as exc:

            mark_queue_failed(
                item["pin_id"],
                str(exc),
            )

            print(f"✗ FAILED: {exc}")
            print()

    print("=" * 60)
    print("PUBLISHER COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()