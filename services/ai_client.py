"""
Atlas AI Client.

Handles all communication with the configured
OpenAI-compatible endpoint (OmniRoute).
"""

from __future__ import annotations

import os

import requests


DEFAULT_BASE_URL = os.getenv(
    "ATLAS_AI_BASE_URL",
    "http://localhost:20128/v1",
)

DEFAULT_MODEL = os.getenv(
    "ATLAS_AI_MODEL",
    "gpt-4o",
)

DEFAULT_API_KEY = os.getenv(
    "ATLAS_AI_API_KEY",
    "atlas-local",
)


class AIClient:
    """
    Atlas AI client.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        api_key: str = DEFAULT_API_KEY,
        timeout: int = 120,
    ) -> None:

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str:
        """
        Generate text using the configured model.
        """

        messages = []

        if system_prompt:

            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data["choices"][0]["message"]["content"]
            .strip()
        )