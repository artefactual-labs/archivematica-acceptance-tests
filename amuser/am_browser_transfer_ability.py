"""Archivematica Transfer Tab Ability."""

import logging
import os
import re

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from . import constants as c
from . import playwright_ability

logger = logging.getLogger("amuser.transfer")


class ArchivematicaBrowserTransferAbility(
    playwright_ability.ArchivematicaPlaywrightAbility
):
    """Archivematica Browser Transfer Tab Ability."""

    def start_transfer(
        self, transfer_path, transfer_name, accession_no=None, transfer_type=None
    ):
        """Start a transfer for ``transfer_path`` named ``transfer_name``."""
        self.navigate_to_transfer_tab()
        name_is_prefix = False
        if transfer_type:
            self.set_transfer_type(transfer_type)
            if transfer_type == "Zipped bag":
                name_is_prefix = True
                transfer_name = os.path.splitext(os.path.basename(transfer_path))[0]
        else:
            transfer_type = "Standard"
        if transfer_type != "Zipped bag":
            self.enter_transfer_name(transfer_name)
        if accession_no:
            self.enter_accession_no(accession_no)
        self.add_transfer_directory(transfer_path)
        self.click_start_transfer_button()

        transfer_uuid, transfer_locator, transfer_name = (
            self.wait_for_transfer_to_appear(
                transfer_name, name_is_prefix=name_is_prefix
            )
        )

        if self.vn < "1.8":
            approve_option_uuid = {
                "Standard": c.APPROVE_STANDARD_TRANSFER_UUID,
                "Zipped bag": c.APPROVE_ZIPPED_BAGIT_TRANSFER_UUID,
            }[transfer_type]
            self.approve_transfer(
                transfer_locator, approve_option_uuid, transfer_name, name_is_prefix
            )
        return transfer_uuid, transfer_name

    def remove_all_transfers(self):
        """Remove all transfers in the Transfer tab."""
        self.navigate_to_transfer_tab()
        try:
            self.wait_for_presence(c.SELECTOR_TRANSFER_DIV)
        except PlaywrightTimeoutError:
            return
        while True:
            top_transfer = self.get_top_transfer()
            if top_transfer is None:
                break
            self.remove_top_transfer(top_transfer)

    def remove_top_transfer(self, top_transfer):
        """Remove the topmost transfer and confirm the operation."""
        transfers = self.page.locator(c.SELECTOR_TRANSFER_DIV)
        transfer_count = transfers.count()
        row = top_transfer.locator("div.sip-row")
        if row.count():
            row.click()
        remove_control = top_transfer.locator("a.btn_remove_sip")
        if not remove_control.count():
            return
        remove_control.click()

        dialog = self.page.locator(
            "div.ui-dialog:visible, div.monitor-modal.monitor-modal-visible:visible"
        ).first
        dialog.wait_for(state="visible")
        confirm = dialog.locator("button.btn.btn-primary")
        if not confirm.count():
            confirm = dialog.get_by_role("button", name="Confirm", exact=True)
        confirm.first.click()
        expect(transfers).to_have_count(
            max(0, transfer_count - 1),
            timeout=self._milliseconds(self.apathetic_wait),
        )

    def get_top_transfer(self):
        """Return the topmost transfer locator, or ``None`` when none exist."""
        transfers = self.page.locator(c.SELECTOR_TRANSFER_DIV)
        if transfers.count():
            return transfers.first
        return None

    def wait_for_transfer_to_appear(self, transfer_name, name_is_prefix=False):
        """Wait for a transfer and return its UUID, locator, and displayed name."""
        transfer_name_selector = "div.sip-detail-directory"
        transfer_uuid_selector = "div.sip-detail-uuid"
        escaped_name = re.escape(transfer_name)
        suffix = r"[\s\S]*" if name_is_prefix else r"\s*(?:UUID)?\s*"
        name_pattern = re.compile(rf"^\s*{escaped_name}{suffix}$")
        name_locator = self.page.locator(
            f"{c.SELECTOR_TRANSFER_DIV} {transfer_name_selector}"
        ).filter(has_text=name_pattern)
        try:
            name_locator.first.wait_for(
                state="attached",
                timeout=self._milliseconds(
                    int(self.max_check_transfer_appeared_attempts)
                    * float(self.quick_wait)
                ),
            )
        except PlaywrightTimeoutError:
            return None, None, None

        name_locator = name_locator.first
        transfer = name_locator.locator(
            "xpath=ancestor::div["
            "contains(concat(' ', normalize-space(@class), ' '), ' sip ')][1]"
        )
        displayed_name = name_locator.inner_text().strip()
        if displayed_name.endswith("UUID"):
            displayed_name = displayed_name[:-4].strip()
        logger.info(
            "Changed transfer name from %s to %s", transfer_name, displayed_name
        )
        abbreviation = name_locator.locator("abbr")
        if abbreviation.count() and abbreviation.is_visible():
            transfer_uuid = abbreviation.get_attribute("title").strip()
        else:
            transfer_uuid = (
                transfer.locator(transfer_uuid_selector).inner_text().strip()
            )
        return transfer_uuid, transfer, displayed_name

    def click_start_transfer_button(self):
        self.page.locator(c.SELECTOR_BUTTON_START_TRANSFER).click()

    def navigate_to_transfer_tab(self):
        """Navigate to Archivematica's Transfer tab and verify its title."""
        url = self.get_transfer_url()
        self.page.goto(url)
        if self.page.url != url:
            self.login()
        self.page.goto(url)
        self.wait_for_presence("#transfer-browser-form")
        assert "Archivematica Dashboard - Transfer" in self.page.title()

    def enter_transfer_name(self, transfer_name):
        self.page.locator(c.SELECTOR_INPUT_TRANSFER_NAME).fill(transfer_name)

    def set_transfer_type(self, transfer_type):
        self.page.locator(c.SELECTOR_INPUT_TRANSFER_TYPE).select_option(
            label=transfer_type
        )

    def enter_accession_no(self, accession_no):
        self.page.locator(c.SELECTOR_INPUT_TRANSFER_ACCESSION).fill(accession_no)

    def click_add_button(self):
        self.page.locator(c.SELECTOR_BUTTON_ADD_DIR_TO_TRANSFER).click()

    def approve_transfer(
        self, transfer_locator, approve_option_uuid, transfer_name, name_is_prefix
    ):
        """Select the requested approval option for a transfer."""
        del transfer_name, name_is_prefix
        option = transfer_locator.locator(f'option[value="{approve_option_uuid}"]')
        option.wait_for(
            state="attached", timeout=self._milliseconds(self.nihilistic_wait)
        )
        option.locator("xpath=..").select_option(value=approve_option_uuid)
