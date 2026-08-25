"""Interact with Archivematica's Vue file browsers."""

import re

from playwright.sync_api import expect

from . import constants as c
from . import playwright_ability


class ArchivematicaBrowserFileExplorerAbility(
    playwright_ability.ArchivematicaPlaywrightAbility
):
    """Navigate the shared Vue tree used for transfers and AIP review."""

    def add_transfer_directory(self, path):
        """Navigate to ``path`` and add it to the transfer."""
        browser = self.page.locator(c.SELECTOR_DIV_TRANSFER_SOURCE_BROWSE)
        if not browser.is_visible():
            self.page.locator(c.SELECTOR_BUTTON_BROWSE_TRANSFER_SOURCES).click()
        browser.wait_for(
            state="visible", timeout=self._milliseconds(self.pessimistic_wait)
        )
        self.navigate_to_transfer_directory_and_click(path)

    def navigate_to_transfer_directory_and_click(self, path):
        """Open every directory in ``path`` and add the selected entry."""
        browser = self.page.locator(c.SELECTOR_DIV_TRANSFER_SOURCE_BROWSE)
        item = self._select_file_browser_path(
            browser, path, label_selector=".tree-node-label > .transfer-node-name"
        )
        expect(item).to_have_attribute(
            "aria-selected", "true", timeout=self._milliseconds(self.medium_wait)
        )
        paths = self.page.locator("#transfer-browser .path-container .path")
        count = paths.count()
        self.click_add_button()
        expect(paths).to_have_count(
            count + 1, timeout=self._milliseconds(self.medium_wait)
        )
        expect(paths.last).to_have_text(
            re.compile(rf"(?:^|/){re.escape(path.strip('/'))}$"),
            timeout=self._milliseconds(self.medium_wait),
        )

    def _select_file_browser_path(
        self, browser, path, *, label_selector=".tree-node-label"
    ):
        """Follow a path in the Vue tree and click its final entry."""
        tree = browser.get_by_role("tree")
        path_parts = path.strip("/").split("/")
        for index, name in enumerate(path_parts):
            # Match this level's own name, excluding child entries and any
            # transfer size or status text displayed beside the name.
            label = self.page.locator(
                f":scope > .tree-node-content > {label_selector}"
            ).filter(has_text=re.compile(rf"^{re.escape(name)}$"))
            item = tree.locator(":scope > [role='treeitem']").filter(has=label)
            item.wait_for(state="visible", timeout=self._milliseconds(self.medium_wait))
            control = item.locator(f":scope > .tree-node-content > {label_selector}")
            if index == len(path_parts) - 1:
                control.click()
                return item
            if item.get_attribute("aria-expanded") != "true":
                control.click()
            expect(item).to_have_attribute(
                "aria-expanded", "true", timeout=self._milliseconds(self.medium_wait)
            )
            tree = item.locator(":scope > [role='group']")
