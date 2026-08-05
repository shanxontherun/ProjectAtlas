from pathlib import Path

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

PROFILE_PATH = Path("browser/profile")


def main() -> None:

    PROFILE_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sync_playwright() as p:

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_PATH),
            headless=False,
            channel="chrome",
        )

        page = context.new_page()

        try:

            page.goto(
                "https://www.pinterest.com/",
                wait_until="domcontentloaded",
                timeout=60000,
            )

        except PlaywrightTimeoutError:

            print("Navigation timed out, continuing anyway...")

        print("=" * 60)
        print("Pinterest opened.")
        print("Log in manually if required.")
        print("After Pinterest is fully loaded, press ENTER here.")
        print("=" * 60)

        input()

        context.close()


if __name__ == "__main__":
    main()