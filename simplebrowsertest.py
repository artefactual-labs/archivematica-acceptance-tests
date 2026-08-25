#!/usr/bin/env python3
"""Smoke-test the Playwright-managed Chrome and Firefox browsers."""

import os
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

TEST_URL = "https://www.artefactual.com"
TEST_TITLE = "Home | Artefactual"


def chrome_executable_path():
    configured_path = os.environ.get("CHROME_EXECUTABLE_PATH")
    if configured_path:
        return configured_path
    chrome_directory = Path(__file__).parent / ".cache" / "chrome"
    candidates = (
        chrome_directory / "chrome",
        chrome_directory
        / "Google Chrome for Testing.app"
        / "Contents"
        / "MacOS"
        / "Google Chrome for Testing",
    )
    return next((str(path) for path in candidates if path.exists()), None)


def run_test(playwright, name):
    print(f"{name}... ", end="")
    browser = None
    try:
        if name == "Chrome":
            executable_path = chrome_executable_path()
            if not executable_path:
                raise RuntimeError(
                    "Chrome is not installed; run `make install-browsers`"
                )
            browser = playwright.chromium.launch(
                headless=True, executable_path=executable_path
            )
        else:
            browser = playwright.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(TEST_URL)
        assert page.title() == TEST_TITLE
        print(f"success! ({browser.version})")
        return 0
    except (AssertionError, PlaywrightError, RuntimeError) as error:
        print("error!", error)
        return 1
    finally:
        if browser:
            browser.close()


if __name__ == "__main__":
    print("Starting tests...")
    with sync_playwright() as playwright_instance:
        chrome_result = run_test(playwright_instance, "Chrome")
        firefox_result = run_test(playwright_instance, "Firefox")
    raise SystemExit(chrome_result or firefox_result)
