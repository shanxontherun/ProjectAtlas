from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

print("Project Root:", PROJECT_ROOT)

sys.path.insert(0, str(PROJECT_ROOT))

print("sys.path[0]:", sys.path[0])

from services.amazon_client import AmazonClient
from services.amazon_bestsellers import fetch_bestsellers


def main():
    client = AmazonClient(headless=False)

    client.open()

    products = fetch_bestsellers(
        client,
        limit=10,
    )

    print(products)

    input("Press ENTER to close...")

    client.close()


if __name__ == "__main__":
    main()