from services.amazon_client import AmazonClient

client = AmazonClient(
    headless=False,
)

client.open()

print(client.page.title())

input("Press ENTER to close...")

client.close()