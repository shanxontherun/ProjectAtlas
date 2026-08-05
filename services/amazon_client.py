"""
Amazon Playwright client.

Uses a persistent browser profile.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)


PROFILE_DIR = (
    Path("browser")
    / "profile"
)


class AmazonClient:

    def __init__(
        self,
        headless: bool = False,
    ) -> None:

        self.playwright: Playwright = sync_playwright().start()

        self.context: BrowserContext = (
            self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=headless,
                viewport={
                    "width": 1400,
                    "height": 900,
                },
            )
        )

        self.page: Page = self.context.pages[0]

    def open(self):

        self.page.goto(
            "https://www.amazon.com/",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        self.page.wait_for_timeout(2000)

    def close(self):

        self.context.close()

        self.playwright.stop()