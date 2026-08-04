"""
AI Service

Handles communication with the configured AI Gateway (OmniRoute).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("AI_BASE_URL")
API_KEY = os.getenv("AI_API_KEY")
MODEL = os.getenv("AI_MODEL")
REQUEST_TIMEOUT = 120

def get_headers() -> dict[str, str]:
    """
    Return the standard headers for AI Gateway requests.
    """
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def test_connection() -> str:
    """
    Sends a simple request to the configured AI gateway.
    """

    if not BASE_URL:
        raise RuntimeError("AI_BASE_URL not configured.")

    if not API_KEY:
        raise RuntimeError("AI_API_KEY not configured.")

    if not MODEL:
        raise RuntimeError("AI_MODEL not configured.")

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=get_headers(),
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": "Reply with exactly: Atlas connected successfully.",
                }
            ],
            "temperature": 0,
            "stream": False,
        },
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]



def load_prompt() -> str:
    """
    Load the Pinterest prompt template.
    """

    prompt_path = Path(__file__).parent.parent / "prompts" / "pinterest_prompt.txt"

    return prompt_path.read_text(encoding="utf-8")

def build_prompt(product: dict) -> str:
    """
    Replace placeholders in the prompt template.
    """

    prompt = load_prompt()

    prompt = prompt.replace(
        "{{product_name}}",
        str(product.get("product_name", "")),
    )

    prompt = prompt.replace(
        "{{category}}",
        str(product.get("category", "")),
    )

    prompt = prompt.replace(
        "{{price}}",
        str(product.get("price", "")),
    )

    prompt = prompt.replace(
        "{{rating}}",
        str(product.get("rating", "")),
    )

    prompt = prompt.replace(
        "{{summary}}",
        str(product.get("ai_summary", "")),
    )

    return prompt
def parse_json_response(content: str) -> dict:
    """
    Parse JSON returned by an AI model, removing Markdown code fences if present.
    """

    content = content.strip()

    if content.startswith("```json"):
        content = content[7:]

    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    return json.loads(content)

def generate_ai_content(product: dict) -> dict:
    """
    Generate AI content for a research product.
    """

    prompt = build_prompt(product)

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=get_headers(),
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.3,
            "stream": False,
        },
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    if "choices" not in data:
        raise RuntimeError(f"Unexpected AI response: {data}")

    content = data["choices"][0]["message"]["content"]
    
    return parse_json_response(content)