"""
Atlas Queue Worker.

Creates Pinterest queue items from generated AI content.
"""

from __future__ import annotations

from services.ai_service import fetch_validated_ai_content
from services.category_routes import fetch_routes_by_category
from services.queue_service import create_queue_item


def main() -> None:
    """
    Entry point for the Queue Worker.
    """

    print("=" * 60)
    print("ATLAS QUEUE WORKER")
    print("=" * 60)

    products = fetch_validated_ai_content()

    print(f"Found {len(products)} AI content record(s).\n")

    created = 0
    skipped = 0
    failed = 0

    for product in products:

        ai_content_id = product["ai_content_id"]
        category_slug = product["category_slug"]
        affiliate_url = product["product_url"]
        image_url = product["image_url"]

        routes = fetch_routes_by_category(category_slug)

        if not routes:
            print(f"[{ai_content_id}] No routes found for '{category_slug}'.")
            skipped += 1
            continue

        for route in routes:

            account_id = route["account_id"]
            board_id = route["board_id"]
            publish_order = route["priority"]

            try:

                create_queue_item(
                    ai_content_id=ai_content_id,
                    account_id=account_id,
                    board_id=board_id,
                    affiliate_url=affiliate_url,
                    image_url=image_url,
                    publish_order=publish_order,
                )

                created += 1

                print(
                    f"[{ai_content_id}] "
                    f"Queued -> Account {account_id}, Board {board_id}"
                )

            except ValueError:

                skipped += 1

                print(
                    f"[{ai_content_id}] "
                    f"Already queued. Skipping."
                )

            except Exception as exc:

                failed += 1

                print(
                    f"[{ai_content_id}] "
                    f"ERROR: {exc}"
                )

    print()
    print("=" * 60)
    print("QUEUE WORKER COMPLETE")
    print("=" * 60)
    print(f"Created : {created}")
    print(f"Skipped : {skipped}")
    print(f"Failed  : {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()