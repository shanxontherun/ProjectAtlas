from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.amazon_client import AmazonClient
from services.amazon_parser import AmazonParser


def main():

    # Use one of the product URLs from our Best Sellers test
    product_url = (
        "https://www.amazon.com/Durable-Honeycomb-Laundry-Delicates-Inches/"
        "dp/B083SCJ8G8/"
    )

    client = AmazonClient(headless=False)
    client.open()

    parser = AmazonParser(client)

    product = parser.parse(product_url)

    print("\n" + "=" * 80)
    print("AMAZON PRODUCT")
    print("=" * 80)

    print(f"ASIN         : {product.asin}")
    print(f"Title        : {product.title}")
    print(f"Brand        : {product.brand}")
    print(f"Price        : {product.price}")
    print(f"Currency     : {product.currency}")
    print(f"Rating       : {product.rating}")
    print(f"Review Count : {product.review_count}")
    print(f"Image URL    : {product.image_url}")
    print(f"Product URL  : {product.product_url}")

    input("\nPress ENTER to close browser...")

    client.close()


if __name__ == "__main__":
    main()