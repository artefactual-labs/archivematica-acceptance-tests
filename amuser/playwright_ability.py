"""Common Playwright browser functionality."""

import logging
import os
import re
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator
from playwright.sync_api import sync_playwright

from . import base

logger = logging.getLogger("amuser.playwright")


class ArchivematicaPlaywrightError(base.ArchivematicaUserError):
    pass


class ArchivematicaPlaywrightAbility(base.Base):
    """Common browser lifecycle and synchronization for browser abilities."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.playwright = None
        self.browser = None
        self.browser_context = None
        self.page = None
        self._tracing_started = False

    @staticmethod
    def _milliseconds(seconds):
        return round(float(seconds) * 1000)

    def set_up(self):
        """Start Playwright and create an isolated browser context and page."""
        self.playwright = sync_playwright().start()
        headless = os.environ.get("HEADLESS") == "1"
        browser_name = self.browser_name.casefold()
        if browser_name == "chrome":
            executable_path = self.chrome_executable_path or os.environ.get(
                "CHROME_EXECUTABLE_PATH"
            )
            if not executable_path:
                local_chrome = Path(self.here) / ".cache" / "chrome"
                candidates = (
                    local_chrome / "chrome",
                    local_chrome
                    / "Google Chrome for Testing.app"
                    / "Contents"
                    / "MacOS"
                    / "Google Chrome for Testing",
                )
                executable_path = next(
                    (str(candidate) for candidate in candidates if candidate.exists()),
                    None,
                )
            launch_options = {"headless": headless}
            if executable_path:
                launch_options["executable_path"] = executable_path
            else:
                raise ArchivematicaPlaywrightError(
                    "Chrome is not installed; run `make install-browsers` or set "
                    "CHROME_EXECUTABLE_PATH"
                )
            self.browser = self.playwright.chromium.launch(**launch_options)
        elif browser_name == "firefox":
            self.browser = self.playwright.firefox.launch(headless=headless)
        else:
            raise ArchivematicaPlaywrightError(
                f'Unsupported browser "{self.browser_name}"; use Chrome or Firefox'
            )

        self.browser_context = self.browser.new_context(
            viewport={"width": 1700, "height": 900}
        )
        self.browser_context.set_default_timeout(
            self._milliseconds(self.pessimistic_wait)
        )
        self.browser_context.set_default_navigation_timeout(
            self._milliseconds(self.apathetic_wait)
        )
        self.browser_context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
        )
        self._tracing_started = True
        self.page = self.browser_context.new_page()

    def tear_down(self, artifact_name=None):
        """Close the browser and optionally retain failure artifacts."""
        try:
            if self.browser_context and self._tracing_started:
                if artifact_name:
                    artifact_dir = Path(self.here) / "output" / "playwright"
                    artifact_dir.mkdir(parents=True, exist_ok=True)
                    safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", artifact_name).strip(
                        "-"
                    )
                    if self.page and not self.page.is_closed():
                        try:
                            self.page.screenshot(
                                path=str(artifact_dir / f"{safe_name}.png"),
                                full_page=True,
                            )
                        except PlaywrightError:
                            logger.exception("Unable to capture Playwright screenshot")
                    self.browser_context.tracing.stop(
                        path=str(artifact_dir / f"{safe_name}-trace.zip")
                    )
                else:
                    self.browser_context.tracing.stop()
                self._tracing_started = False
        finally:
            if self.browser_context:
                self.browser_context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.page = None
            self.browser_context = None
            self.browser = None
            self.playwright = None
            self.clear_tmp_dir()

    def navigate(self, url, reload=False):
        """Navigate to ``url``; log in and try again when redirected."""
        if self.page.url == url and not reload:
            return
        self.page.goto(url)
        if self.page.url == url:
            return
        if self.page.url.endswith("/installer/welcome/"):
            self.setup_new_install()
        elif url.startswith(self.ss_url):
            self.login_ss()
        else:
            self.login()
        self.page.goto(url)

    def wait_for_presence(self, selector, timeout=None):
        self.page.locator(selector).first.wait_for(
            state="attached",
            timeout=self._milliseconds(timeout or self.nihilistic_wait),
        )

    def wait_for_invisibility(self, selector, timeout=None):
        self.page.locator(selector).first.wait_for(
            state="hidden",
            timeout=self._milliseconds(timeout or self.nihilistic_wait),
        )

    def wait_for_visibility(self, selector, timeout=None):
        self.page.locator(selector).first.wait_for(
            state="visible",
            timeout=self._milliseconds(timeout or self.nihilistic_wait),
        )

    def wait_for_table_filter(
        self, table_selector, search_term, empty_selector=None, timeout=None
    ):
        """Wait until a client-side table reflects ``search_term``."""
        tokens = [
            (quoted or bare).strip().casefold()
            for quoted, bare in re.findall(r'"([^"]+)"|(\S+)', search_term)
            if (quoted or bare).strip()
        ]
        self.page.wait_for_function(
            """
            ({ tableSelector, emptySelector, tokens }) => {
              const table = document.querySelector(tableSelector);
              if (!table) return false;

              const empty = emptySelector
                ? document.querySelector(emptySelector)
                : null;
              if (empty && !/loading|processing/i.test(empty.textContent || '')) {
                return true;
              }

              const rows = Array.from(table.querySelectorAll('tbody tr'));
              if (rows.length === 0) return false;
              if (rows.length === 1) {
                const cells = rows[0].querySelectorAll('td');
                const text = (rows[0].textContent || '').trim();
                if (cells.length === 1 && /no matching|no records/i.test(text)) {
                  return true;
                }
                if (/loading|processing/i.test(text)) return false;
              }
              return rows.every((row) => {
                const text = (row.textContent || '').toLocaleLowerCase();
                return tokens.every((token) => text.includes(token));
              });
            }
            """,
            arg={
                "tableSelector": table_selector,
                "emptySelector": empty_selector,
                "tokens": tokens,
            },
            timeout=self._milliseconds(timeout or self.pessimistic_wait),
        )

    def wait(self, seconds):
        """Yield to Playwright while polling application state."""
        self.page.wait_for_timeout(self._milliseconds(seconds))

    def hover(self, locator: Locator):
        locator.hover()

    def body_text(self):
        return self.page.locator("body").inner_text()

    @contextmanager
    def temporary_page(self):
        """Temporarily make a new page active without losing the main page."""
        original_page = self.page
        page = self.browser_context.new_page()
        self.page = page
        try:
            yield page
        finally:
            if not page.is_closed():
                page.close()
            self.page = original_page
