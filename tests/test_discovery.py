from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.amazon_client import AmazonClient
from services.discovery_service import DiscoveryService


client = AmazonClient(
    headless=False,
)

client.open()

service = DiscoveryService(client)

products = service.discover(limit=5)

print()

for product in products:

    print(product.model_dump())

input()

client.close()