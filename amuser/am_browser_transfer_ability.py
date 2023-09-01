"""Archivematica Transfer Tab Ability"""
import logging
import os
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select

from . import constants as c
from . import selenium_ability


logger = logging.getLogger("amuser.transfer")


class ArchivematicaBrowserTransferAbility(
    selenium_ability.ArchivematicaSeleniumAbility
):
    """Archivematica Browser Transfer Tab Ability."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.check_transfer_appeared_attempts = 0

    def start_transfer(
        self, transfer_path, transfer_name, accession_no=None, transfer_type=None
    ):
        """Start a new transfer with name ``transfer_name``, transfering the
        directory at ``transfer_path``.
        :param str transfer_path: the path to the transfer to be started as it
            appears in the AM file explorer interface; should not start or end
            with a forward slash.
        :param str transfer_name: the name of the transfer; should be a valid
            AM transfer name, i.e., one that AM will not alter. This is because
            the name is used to re-identify the transfer from the DOM data.
            Should match /[a-zA-Z0-9_]+/.
        """
        self.navigate_to_transfer_tab()
        name_is_prefix = False
        if transfer_type:
            self.set_transfer_type(transfer_type)
            # For some reason selecting a transfer type can cause the window to
            # scroll and will prevent Selenium from clicking the "Browse"
            # button so the following line is necessary.
            self.driver.execute_script("window.scrollTo(0, 0);")
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

        (
            transfer_uuid,
            transfer_div_elem,
            transfer_name,
        ) = self.wait_for_transfer_to_appear(
            transfer_name, name_is_prefix=name_is_prefix
        )

        # In Archivematica 1.8 transfers can be automatically approved. This
        # is the default in the system. Use the ``am_version`` flag to make
        # sure that approval is not a required step for tests >= 1.8.
        if self.vn < "1.8":
            # UUID for the "Approve transfer" option
            approve_option_uuid = {
                "Standard": c.APPROVE_STANDARD_TRANSFER_UUID,
                "Zipped bag": c.APPROVE_ZIPPED_BAGIT_TRANSFER_UUID,
            }[transfer_type]
            self.approve_transfer(
                transfer_div_elem, approve_option_uuid, transfer_name, name_is_prefix
            )
        return transfer_uuid, transfer_name

    def remove_all_transfers(self):
        """Remove all transfers in the Transfers tab."""
        self.navigate_to_transfer_tab()
        self.wait_for_presence(c.SELECTOR_TRANSFER_DIV, self.nihilistic_wait)
        while True:
            top_transfer_elem = self.get_top_transfer()
            if not top_transfer_elem:
                break
            self.remove_top_transfer(top_transfer_elem)

    def remove_top_transfer(self, top_transfer_elem):
        """Remove the topmost transfer: click on its "Remove" button and click
        "Confirm".
        """
        remove_elem = top_transfer_elem.find_element_by_css_selector("a.btn_remove_sip")
        if remove_elem:
            remove_elem.click()
            dialog_selector = "div.ui-dialog"
            self.wait_for_presence(dialog_selector)
            remove_sip_confirm_dialog_elems = self.driver.find_elements_by_css_selector(
                "div.ui-dialog"
            )
            for dialog_elem in remove_sip_confirm_dialog_elems:
                if dialog_elem.is_displayed():
                    remove_sip_confirm_dialog_elem = dialog_elem
                    break
            for (
                button_elem
            ) in remove_sip_confirm_dialog_elem.find_elements_by_css_selector("button"):
                if button_elem.text.strip() == "Confirm":
                    button_elem.click()
            self.wait_for_invisibility(dialog_selector)
            try:
                while top_transfer_elem.is_displayed():
                    time.sleep(self.quick_wait)
            except StaleElementReferenceException:
                pass

    def get_top_transfer(self):
        """Get the topmost transfer ('.sip') <div> in the transfers tab."""
        transfer_elems = self.driver.find_elements_by_css_selector(
            c.SELECTOR_TRANSFER_DIV
        )
        if transfer_elems:
            return transfer_elems[0]
        return None

    def wait_for_transfer_to_appear(self, transfer_name, name_is_prefix=False):
        """Wait until the transfer appears in the transfer tab (after "Start
        transfer" has been clicked). The only way to do this seems to be to
        check each row for our unique ``transfer_name`` and do
        ``time.sleep(self.micro_wait)`` until it appears, or a max number of
        waits is exceeded.
        Returns the transfer UUID and the transfer <div> element.
        """
        transfer_name_div_selector = "div.sip-detail-directory"
        transfer_uuid_div_selector = "div.sip-detail-uuid"
        self.wait_for_presence(transfer_name_div_selector)
        transfer_uuid = correct_transfer_div_elem = None
        for transfer_div_elem in self.driver.find_elements_by_css_selector(
            c.SELECTOR_TRANSFER_DIV
        ):
            transfer_name_div_elem = transfer_div_elem.find_element_by_css_selector(
                transfer_name_div_selector
            )
            transfer_uuid_div_elem = transfer_div_elem.find_element_by_css_selector(
                transfer_uuid_div_selector
            )
            # Identify the transfer by its name. The complication here is that
            # AM detects a narrow browser window and hides the UUID in the
            # narrow case. So depending on the visibility/width of things, we
            # find the UUID in different places.
            transfer_name_in_dom = transfer_name_div_elem.text.strip()
            if transfer_name_in_dom.endswith("UUID"):
                transfer_name_in_dom = transfer_name_in_dom[:-4].strip()
            if name_is_prefix:
                cond = transfer_name_in_dom.startswith(transfer_name)
            else:
                cond = transfer_name_in_dom == transfer_name
            if cond:
                logger.info(
                    "Changed transfer name from %s to %s",
                    transfer_name,
                    transfer_name_in_dom,
                )
                transfer_name = transfer_name_in_dom
                abbr_elem = transfer_name_div_elem.find_element_by_tag_name("abbr")
                if abbr_elem and abbr_elem.is_displayed():
                    transfer_uuid = abbr_elem.get_attribute("title").strip()
                else:
                    transfer_uuid = transfer_uuid_div_elem.text.strip()
                correct_transfer_div_elem = transfer_div_elem
        if not transfer_uuid:
            self.check_transfer_appeared_attempts += 1
            if (
                self.check_transfer_appeared_attempts
                < self.max_check_transfer_appeared_attempts
            ):
                time.sleep(self.quick_wait)
                (
                    transfer_uuid,
                    correct_transfer_div_elem,
                    transfer_name,
                ) = self.wait_for_transfer_to_appear(
                    transfer_name, name_is_prefix=name_is_prefix
                )
            else:
                self.check_transfer_appeared_attempts = 0
                return None, None, None
        time.sleep(self.quick_wait)
        return transfer_uuid, correct_transfer_div_elem, transfer_name

    def click_start_transfer_button(self):
        start_transfer_button_elem = self.driver.find_element_by_css_selector(
            c.SELECTOR_BUTTON_START_TRANSFER
        )
        start_transfer_button_elem.click()

    def navigate_to_transfer_tab(self):
        """Navigate to Archivematica's Transfer tab and make sure it worked."""
        url = self.get_transfer_url()
        self.driver.get(url)
        if self.driver.current_url != url:
            self.login()
        self.driver.get(url)
        transfer_name_input_id = "transfer-browser-form"
        self.wait_for_presence(f"#{transfer_name_input_id}")
        assert "Archivematica Dashboard - Transfer" in self.driver.title

    def enter_transfer_name(self, transfer_name):
        """Enter a transfer name into the text input."""
        # transfer_name_elem = self.driver.find_element_by_id('transfer-name')
        transfer_name_elem = self.driver.find_element_by_css_selector(
            c.SELECTOR_INPUT_TRANSFER_NAME
        )
        transfer_name_elem.send_keys(transfer_name)

    def set_transfer_type(self, transfer_type):
        """Select transfer type ``transfer_type`` in the <select> input."""
        transfer_type_select_el = self.driver.find_element_by_css_selector(
            c.SELECTOR_INPUT_TRANSFER_TYPE
        )
        transfer_type_select = Select(transfer_type_select_el)
        transfer_type_select.select_by_visible_text(transfer_type)

    def enter_accession_no(self, accession_no):
        accession_no_elem = self.driver.find_element_by_css_selector(
            c.SELECTOR_INPUT_TRANSFER_ACCESSION
        )
        accession_no_elem.send_keys(accession_no)

    def click_add_button(self):
        """Click "Add" button to add directories to transfer."""
        self.driver.find_element_by_css_selector(
            c.SELECTOR_BUTTON_ADD_DIR_TO_TRANSFER
        ).click()

    def approve_transfer(
        self, transfer_div_elem, approve_option_uuid, transfer_name, name_is_prefix
    ):
        """Click the "Approve transfer" select option to initiate the transfer
        process.

        TODO/WARNING: this some times triggers ElementNotVisibleException
        when the click is attempted. Potential solution: catch exception and
        re-click the micro-service <div> to make the hidden <select> visible
        again.
        """
        approve_transfer_option_selector = "option[value='{}']".format(
            approve_option_uuid
        )
        while True:
            try:
                approve_transfer_option = (
                    transfer_div_elem.find_element_by_css_selector(
                        approve_transfer_option_selector
                    )
                )
            except NoSuchElementException:
                logger.info(
                    "NoSuchElementException raised when attempting to"
                    " retrieve element with css selector %s",
                    approve_transfer_option_selector,
                )
                time.sleep(self.optimistic_wait)
            else:
                break
        try:
            select_el = approve_transfer_option.find_element_by_xpath("..")
            select_inst = Select(select_el)
            select_inst.select_by_value(approve_option_uuid)
        except StaleElementReferenceException:
            # Get a new transfer <div> element and recurse.
            logger.info(
                "The select element has gone stale before we could use"
                " it to approve the transfer. Trying again with a new"
                " one."
            )
            _, transfer_div_elem, transfer_name = self.wait_for_transfer_to_appear(
                transfer_name, name_is_prefix=name_is_prefix
            )
            self.approve_transfer(
                transfer_div_elem, approve_option_uuid, transfer_name, name_is_prefix
            )
