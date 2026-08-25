"""Archivematica Browser File Explorer Ability."""

import logging

from . import constants as c
from . import playwright_ability

logger = logging.getLogger("amuser.fileexplorer")


class ArchivematicaBrowserFileExplorerAbility(
    playwright_ability.ArchivematicaPlaywrightAbility
):
    """Interact with Archivematica's old and new file explorers."""

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
        """Open every directory in ``path`` and add the leaf directory."""
        self._navigate_to_transfer_directory_and_click(path)

    def _navigate_to_transfer_directory_and_click(self, path):
        xtrail = []
        path_parts = path.strip("/").split("/")
        for index, folder in enumerate(path_parts):
            logger.info('Opening file explorer entry "%s"', folder)
            folder_label_xpath = get_xpath_matches_folder_text(folder)
            if index == 0:
                folder_label_xpath = f"//{folder_label_xpath}"
            xtrail.append(folder_label_xpath)
            folder_label_xpath = c.XPATH_TREEITEM_NEXT_SIBLING.join(xtrail)
            folder_label = self.page.locator(f"xpath={folder_label_xpath}")
            folder_label.wait_for(
                state="visible", timeout=self._milliseconds(self.pessimistic_wait)
            )
            folder_label.scroll_into_view_if_needed()
            if index == len(path_parts) - 1:
                self.click_folder_label(folder_label)
                self.click_add_button()
            else:
                self.click_folder(folder_label_xpath)

    def click_add_folder(self, folder_id):
        """Click Add for a directory in the old file explorer."""
        folder = self.page.locator(f'[id="{folder_id}"]')
        folder.wait_for(state="visible", timeout=self._milliseconds(self.medium_wait))
        folder.hover()
        action = folder.locator(f"span.{c.CLASS_ADD_TRANSFER_FOLDER}")
        action.hover()
        action.click()

    def click_file(self, file_id):
        """Click a file in the new file explorer."""
        self.click_folder(file_id, is_file=True)

    def click_file_old_browser(self, file_id):
        """Click a file in the old file explorer."""
        self.click_folder_old_browser(file_id, is_file=True)

    def click_folder_label(self, folder):
        """Select a directory and wait until it can be added."""
        folder.scroll_into_view_if_needed()
        folder.click()
        self.page.locator(c.SELECTOR_BUTTON_ADD_DIR_TO_TRANSFER).wait_for(
            state="visible", timeout=self._milliseconds(self.medium_wait)
        )

    def click_folder(self, folder_label_xpath, is_file=False):
        """Open an entry in the new file explorer."""
        if folder_label_xpath.startswith("/"):
            folder_label = self.page.locator(f"xpath={folder_label_xpath}")
        else:
            folder_label = self.page.locator(f'[id="{folder_label_xpath}"]')
        folder_label.wait_for(
            state="visible", timeout=self._milliseconds(self.medium_wait)
        )
        folder_label.scroll_into_view_if_needed()
        if is_file:
            folder_label.click()
            return
        folder_icon = self.page.locator(
            f"xpath={folder_label2icon_xpath(folder_label_xpath)}"
        )
        folder_icon.click()
        self.page.locator(
            f"xpath={folder_label2children_xpath(folder_label_xpath)}"
        ).wait_for(state="visible", timeout=self._milliseconds(self.medium_wait))

    def click_folder_old_browser(self, folder_id, is_file=False):
        """Open an entry in the old Backbone file explorer."""
        folder = self.page.locator(f'[id="{folder_id}"]')
        folder.wait_for(state="visible", timeout=self._milliseconds(self.medium_wait))
        folder.hover()
        class_name = "backbone-file-explorer-directory_icon_button"
        if is_file:
            class_name = "backbone-file-explorer-directory_entry_name"
        control = folder.locator(f"span.{class_name}")
        control.hover()
        control.click()
        if is_file:
            return
        folder.locator(
            "xpath=following-sibling::div[contains(@class, "
            "'backbone-file-explorer-level')]"
        ).wait_for(state="visible", timeout=self._milliseconds(self.medium_wait))


def get_xpath_matches_folder_text(folder_text):
    """Return an XPath matching a named folder in the transfer browser."""
    return (
        "div[contains(@class, 'tree-label') and"
        f" descendant::span[starts-with(normalize-space(text()), '{folder_text}') and"
        " starts-with(normalize-space(substring-after("
        "normalize-space(text()),"
        f" '{folder_text}')), '(')]]"
    )


def folder_label2icon_xpath(folder_label_xpath):
    """Return the folder icon XPath for a folder-label XPath."""
    return f"{folder_label_xpath}/preceding-sibling::i[@class='tree-branch-head']"


def folder_label2children_xpath(folder_label_xpath):
    """Return the children XPath for a folder-label XPath."""
    return f"{folder_label_xpath}/following-sibling::treeitem"
