from services.amazon_client import AmazonClient

client = AmazonClient(headless=False)

client.open()

client.page.goto(
    "https://www.amazon.com/s?k=kitchen+storage",
    wait_until="domcontentloaded",
)

client.page.wait_for_timeout(5000)

cards = client.page.locator(
    "div[data-component-type='s-search-result']"
)

print(f"Cards found: {cards.count()}")

first = cards.nth(0)

print("\n===== FIRST CARD HTML =====\n")
print(first.inner_html())

input("\nPress ENTER to close...")

client.close()