from services.ai_client import AIClient


client = AIClient()

response = client.generate(
    prompt="Reply with exactly: Atlas is working.",
)

print(response)