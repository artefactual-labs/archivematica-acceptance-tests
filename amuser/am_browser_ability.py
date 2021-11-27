"""Archivematica Browser Ability

This module contains the ``ArchivematicaBrowserAbility`` class, which encodes
the ability of an Archivematica user to use a browser to interact with
Archivematica. This class provides an interface to Selenium for opening browser
windows and interacting with Archivematica's GUIs.
"""

import logging
import time

import requests
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    ElementNotInteractableException,
    ElementNotVisibleException,
    NoSuchElementException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from . import constants as c
from . import base
from . import am_browser_auth_ability as auth_abl
from . import am_browser_transfer_ingest_ability as tra_ing_abl
from . import am_browser_ss_ability as ss_abl
from . import am_browser_preservation_planning_ability as pres_plan_abl


logger = logging.getLogger("amuser.browser")


class ArchivematicaBrowserAbilityError(base.ArchivematicaUserError):
    pass


class ArchivematicaBrowserAbility(
    auth_abl.ArchivematicaBrowserAuthenticationAbility,
    tra_ing_abl.ArchivematicaBrowserTransferIngestAbility,
    ss_abl.ArchivematicaBrowserStorageServiceAbility,
    pres_plan_abl.ArchivematicaBrowserPreservationPlanningAbility,
):
    """Archivematica Browser Ability: the ability of an Archivematica user to
    use a browser to interact with Archivematica. A class for using Selenium to
    interact with a live Archivematica instance.
    """

    @property
    def ss_api_key(self):
        if not self._ss_api_key:
            self.driver.get(self.get_ss_login_url())
            self.driver.find_element_by_id("id_username").send_keys(self.ss_username)
            self.driver.find_element_by_id("id_password").send_keys(self.ss_password)
            self.driver.find_element_by_css_selector(
                c.varvn("SELECTOR_SS_LOGIN_BUTTON", self.vn)
            ).click()
            self.driver.get(self.get_default_ss_user_edit_url())
            block = WebDriverWait(self.driver, 20)
            block.until(EC.presence_of_element_located((By.CSS_SELECTOR, "code")))
            self._ss_api_key = self.driver.find_element_by_tag_name("code").text.strip()
        return self._ss_api_key

    def get_displayed_tabs(self):
        ret = []
        for li_el in self.driver.find_element_by_css_selector(
            "ul.navbar-nav"
        ).find_elements_by_tag_name("li"):
            ret.append(li_el.text.strip().split("\n")[0])
        return list(filter(None, ret))

    def assert_sip_arrange_pane_not_displayed(self):
        for selector in ("form#search_form", "div#originals", "div#arrange"):
            try:
                self.driver.find_element_by_css_selector(selector)
            except NoSuchElementException as exc:
                assert "Unable to locate element: {}".format(selector) in str(exc)
        assert self.driver.find_element_by_css_selector("div#sip-container")

    # ==========================================================================
    # Archival Storage Tab
    # ==========================================================================

    def wait_for_aip_in_archival_storage(self, aip_uuid):
        """Wait for the AIP with UUID ``aip_uuid`` to appear in the Archival
        storage tab.
        """
        max_attempts = self.max_search_aip_archival_storage_attempts
        attempts = 0
        while True:
            self.navigate(self.get_archival_storage_url(), reload=True)
            self.driver.find_element_by_css_selector(
                'input[title="search query"]'
            ).send_keys(aip_uuid)
            Select(
                self.driver.find_element_by_css_selector('select[title="field name"]')
            ).select_by_visible_text("AIP UUID")
            Select(
                self.driver.find_element_by_css_selector('select[title="query type"]')
            ).select_by_visible_text("Phrase")
            self.driver.find_element_by_id("search_submit").click()
            self.wait_for_presence("#archival-storage-entries_info")
            summary_el = self.driver.find_element_by_id("archival-storage-entries_info")
            if summary_el.text.strip() == "Showing 0 to 0 of 0 entries":
                attempts += 1
                if attempts > max_attempts:
                    break
                time.sleep(self.optimistic_wait)
            else:
                time.sleep(
                    self.optimistic_wait
                )  # Sleep a little longer, for good measure
                break

    def request_aip_delete(self, aip_uuid):
        """Request the deletion of the AIP with UUID ``aip_uuid`` using the
        dashboard GUI.
        """
        self.navigate_to_aip_in_archival_storage(aip_uuid)
        delete_tab_selector = 'a[href="#tab-delete"]'
        self.wait_for_presence(delete_tab_selector, timeout=self.apathetic_wait)
        while True:
            try:
                self.driver.find_element_by_id("id_delete-uuid").click()
                break
            except (ElementNotVisibleException, ElementNotInteractableException):
                self.driver.find_element_by_css_selector(delete_tab_selector).click()
                time.sleep(self.optimistic_wait)
        self.driver.find_element_by_id("id_delete-uuid").send_keys(aip_uuid)
        self.driver.find_element_by_id("id_delete-reason").send_keys("Cuz wanna")
        self.driver.find_element_by_css_selector(
            'button[name="submit-delete-form"]'
        ).click()
        alert_text = self.driver.find_element_by_css_selector(
            "div.alert-info"
        ).text.strip()
        assert alert_text == "Delete request created successfully."

    def navigate_to_aip_in_archival_storage(self, aip_uuid):
        url = self.get_aip_in_archival_storage_url(aip_uuid)
        max_attempts = self.max_navigate_aip_archival_storage_attempts
        attempt = 0
        s = requests.session()
        s.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML,"
                " like Gecko) Chrome/44.0.2403.157 Safari/537.36"
            }
        )
        for cookie in self.driver.get_cookies():
            s.cookies.update({cookie["name"]: cookie["value"]})
        while True:
            if attempt > max_attempts:
                raise ArchivematicaBrowserAbilityError(
                    "Unable to navigate to {}".format(url)
                )
            r = s.get(url)
            if r.status_code == requests.codes.ok:
                logger.info(
                    "Requests got OK status code %s when requesting %s",
                    r.status_code,
                    url,
                )
                break
            logger.info(
                "Requests got bad status code %s when requesting"
                " %s; waiting for 1 second before trying"
                " again",
                r.status_code,
                url,
            )
            attempt += 1
            time.sleep(self.optimistic_wait)
        self.navigate(url, reload=True)

    def initiate_reingest(self, aip_uuid, reingest_type="metadata-only"):
        self.navigate_to_aip_in_archival_storage(aip_uuid)
        reingest_tab_selector = 'a[href="#tab-reingest"]'
        self.wait_for_presence(reingest_tab_selector, timeout=self.apathetic_wait)
        type_selector = {
            "metadata-only": "input#id_reingest-reingest_type_1",
            "metadata-and-objects": "input#id_reingest-reingest_type_2",
        }.get(reingest_type)
        if not type_selector:
            raise ArchivematicaBrowserAbilityError(
                "Unable to initiate a reingest of type {} on AIP"
                " {}".format(reingest_type, aip_uuid)
            )
        while True:
            type_input_el = self.driver.find_element_by_css_selector(type_selector)
            if type_input_el.is_displayed():
                break
            else:
                self.driver.find_element_by_css_selector(reingest_tab_selector).click()
                time.sleep(self.optimistic_wait)
        self.driver.find_element_by_css_selector(type_selector).click()
        self.driver.find_element_by_css_selector(
            "button[name=submit-reingest-form]"
        ).click()
        self.wait_for_visibility("div.alert-success")
        alert_text = self.driver.find_element_by_css_selector(
            "div.alert-success"
        ).text.strip()
        assert alert_text.startswith("Package {} sent to pipeline".format(aip_uuid))
        assert alert_text.endswith("for re-ingest")

    # ==========================================================================
    # Transfer Backlog Tab
    # ==========================================================================

    def wait_for_dip_in_transfer_backlog(self, dip_uuid):
        """Wait for the DIP with UUID ``dip_uuid`` to appear in the Backlog tab.
        """
        max_seconds = self.max_search_dip_backlog_attempts
        seconds = 0
        while True:
            self.navigate(self.get_transfer_backlog_url(), reload=True)
            self.driver.find_element_by_css_selector(
                'input[title="search query"]'
            ).send_keys(dip_uuid)
            Select(
                self.driver.find_element_by_css_selector('select[title="field name"]')
            ).select_by_visible_text("Transfer UUID")
            Select(
                self.driver.find_element_by_css_selector('select[title="query type"]')
            ).select_by_visible_text("Phrase")
            self.driver.find_element_by_id("search_submit").click()
            self.wait_for_presence("#backlog-entries_info")
            summary_el = self.driver.find_element_by_id("backlog-entries_info")
            if summary_el.text.strip() == "Showing 0 to 0 of 0 entries":
                seconds += 1
                if seconds > max_seconds:
                    logger.warning(
                        "In waiting for DIP %s to appear in the"
                        " transfer backlog, we exceeded the maximum"
                        " wait period of %s seconds.",
                        dip_uuid,
                        max_seconds,
                    )
                    break
                time.sleep(self.medium_wait)
            else:
                logger.info(
                    "Found DIP %s in the transfer backlog after waiting"
                    " for %s seconds.",
                    dip_uuid,
                    seconds,
                )
                time.sleep(self.medium_wait)  # Sleep a little longer, for good measure
                break

    # ==========================================================================
    # Administration Tab
    # ==========================================================================

    def upload_policy(self, policy_path):
        self.navigate_to_policies()
        self.driver.execute_script(
            "document.getElementById('file').style.display='block'"
        )
        self.driver.find_element_by_css_selector("input[name=file]").send_keys(
            policy_path
        )
        self.driver.find_element_by_css_selector("input[type=submit]").click()

    def navigate_to_policies(self):
        self.navigate(self.get_policies_url())

    def configure_handle(self, **kwargs):
        """Navigate to the "Handle server config" page in the dashboard and
        input all of the values in the ``**kwargs`` dict. Note: each key in
        ``kwargs`` must be a valid id value of an <input> or <select> element
        in the form when 'id_' is prefixed to it.
        """
        self.navigate(self.get_handle_config_url())
        for key, val in kwargs.items():
            dom_id = "id_" + key
            input_el = self.driver.find_element_by_id(dom_id)
            if input_el.tag_name == "select":
                Select(input_el).select_by_visible_text(val)
            elif input_el.get_attribute("type") == "checkbox":
                state = input_el.get_attribute("checked")
                if (val is True and state != "true") or (
                    val is False and state == "true"
                ):
                    input_el.click()
            else:
                input_el.clear()
                input_el.send_keys(val)
        submit_button = self.driver.find_element_by_css_selector("input[type=submit]")
        submit_button.click()
        self.wait_for_visibility("div.alert-info")
        assert (
            self.driver.find_element_by_css_selector(".alert-info").text.strip()
            == "Saved."
        ), "Unable to confirm saving of Handle configuration"

    def get_es_indexing_config_text(self):
        self.navigate(self.get_admin_general_url())
        try:
            el = self.driver.find_element_by_css_selector("p.es-indexing-configuration")
        except NoSuchElementException:
            return None
        else:
            return el.text

    # =========================================================================
    # Processing Configuration
    # =========================================================================

    def reset_default_processing_config(self):
        self.navigate(self.get_reset_default_processing_config_url())

    def save_default_processing_config(self):
        """Click the "Save" button in the default processing config edit
        interface.
        """
        edit_default_processing_config_url = (
            self.get_edit_default_processing_config_url()
        )
        if self.driver.current_url != edit_default_processing_config_url:
            self.navigate(edit_default_processing_config_url)
        self.driver.find_element_by_css_selector("input[value=Save]").click()

    def get_processing_config_decision_options(self, **kwargs):
        """Return the options available for a given processing config decision
        as a list of strings.
        """
        decision_id = kwargs.get("decision_id")  # 'id_<UUID>' or just '<UUID>'
        decision_label = kwargs.get("decision_label")  # e.g., 'Select
        # compression algorithm'
        if decision_id is None and decision_label is None:
            raise ArchivematicaBrowserAbilityError(
                "You must provide a decision id or a decision label when"
                " getting the available options for a processing config"
                " decision"
            )
        # Make sure we are editing the default processing config and
        # navigate there if not.
        edit_default_processing_config_url = (
            self.get_edit_default_processing_config_url()
        )
        if self.driver.current_url != edit_default_processing_config_url:
            self.navigate(edit_default_processing_config_url)
        # Get a decision_id value, something of the form 'id_<UUID>'
        if decision_id is None:
            decision_id = _get_decision_id_from_label(decision_label)
        else:
            if not decision_id.startswith("id_"):
                decision_id = "id_" + decision_id
        decision_el = self.driver.find_element_by_id(decision_id)
        options = []
        if decision_el.tag_name == "select":
            for option_el in decision_el.find_elements_by_tag_name("option"):
                options.append(option_el.text.strip())
        return options

    def set_processing_config_decision(self, **kwargs):
        """Set the (default) processing config decision, identified via
        ``decision_id`` or ``decision_label``) to the value/choice
        identified via ``choice_*``.

        The idea is for this method to be flexible: users can supply
        decision/choice strings and hope we identify them correctly, or
        they can use UUID-based decision ids and choice names to be
        explicit.
        """
        decision_id = kwargs.get("decision_id")  # 'id_<UUID>' or just '<UUID>'
        decision_label = kwargs.get("decision_label")  # e.g., 'Select
        # compression algorithm'
        choice_value_attr = kwargs.get("choice_value_attr")  # '<UUID>'
        choice_value = kwargs.get("choice_value")  # e.g., '7z using bzip2'
        choice_index = kwargs.get("choice_index")  # e.g., 0
        if decision_id is None and decision_label is None:
            raise ArchivematicaBrowserAbilityError(
                "You must provide a decision id or a decision label when"
                " setting a processing config decision"
            )
        if choice_value_attr is None and choice_value is None and choice_index is None:
            raise ArchivematicaBrowserAbilityError(
                "You must provide a choice value attribute, a choice value"
                " (text) or a choice index when setting a processing config"
                " decision"
            )
        # Make sure we are editing the default processing config and
        # navigate there if not.
        edit_default_processing_config_url = (
            self.get_edit_default_processing_config_url()
        )
        if self.driver.current_url != edit_default_processing_config_url:
            self.navigate(edit_default_processing_config_url)
        # Get a decision_id value, something of the form 'id_<UUID>'
        if decision_id is None:
            decision_id = _get_decision_id_from_label(decision_label)
        else:
            if not decision_id.startswith("id_"):
                decision_id = "id_" + decision_id
        decision_el = self.driver.find_element_by_id(decision_id)
        if decision_el.tag_name == "select":
            decision_select = Select(decision_el)
            if choice_value_attr is not None:
                decision_select.select_by_value(choice_value_attr)
            elif choice_index is not None:
                decision_select.select_by_index(choice_index)
            else:
                decision_select.select_by_visible_text(choice_value)
        else:
            # Assume it is <input[type=text]>
            decision_el.clear()
            decision_el.send_keys(choice_value)

    def ensure_default_processing_config_in_default_state(self):
        """Make sure that the default processing config is in its default
        state.

        The following JavaScript in the browser console will summarize the
        needed details of the default state of the default processing config::

            $('table tr').each(function(){
                $(this).find('td').each(function(){
                    var label = $(this).find('label');
                    var select = $(this).find('select');
                    if (label.length>0) {
                        console.log(label.text());
                    } else if (select.length>0) {
                        console.log(select.attr('id'));
                        console.log(select.find(":selected").text());
                        console.log(select.find(":selected").attr('value'));
                    }
                })
            });
        """
        self.set_processing_config_decision(
            decision_label="Generate transfer structure report", choice_value="No"
        )
        self.set_processing_config_decision(
            decision_label=("Perform file format identification (Transfer)"),
            choice_value="None",
        )
        self.set_processing_config_decision(
            decision_label="Extract packages", choice_value="Yes"
        )
        self.set_processing_config_decision(
            decision_label="Delete packages after extraction", choice_value="Yes"
        )
        self.set_processing_config_decision(
            decision_label="Examine contents", choice_value="Skip examine contents"
        )
        self.set_processing_config_decision(
            decision_label="Create SIP(s)", choice_value="None"
        )
        self.set_processing_config_decision(
            decision_label="Perform file format identification (Ingest)",
            choice_value="No, use existing data",
        )
        self.set_processing_config_decision(
            decision_label="Normalize", choice_value="None"
        )
        self.set_processing_config_decision(
            decision_label="Approve normalization", choice_value="None"
        )
        self.set_processing_config_decision(
            decision_label="Reminder: add metadata if desired", choice_value="Continue"
        )
        self.set_processing_config_decision(
            decision_label="Transcribe files (OCR)", choice_value="No"
        )
        self.set_processing_config_decision(
            decision_label=(
                "Perform file format identification (Submission documentation & metadata)"
            ),
            choice_value="None",
        )
        self.set_processing_config_decision(
            decision_label="Select compression algorithm", choice_value="7z using bzip2"
        )
        self.set_processing_config_decision(
            decision_label="Select compression level",
            choice_value="5 - normal compression",
        )
        self.set_processing_config_decision(
            decision_label="Store AIP", choice_value="None"
        )
        self.set_processing_config_decision(
            decision_label="Store AIP location", choice_value="None"
        )
        self.set_processing_config_decision(
            decision_label="Store DIP location", choice_value="None"
        )
        if self.vn in ("1.7", "1.8"):
            self.set_processing_config_decision(
                decision_label="Perform policy checks on access derivatives",
                choice_value="None",
            )
            self.set_processing_config_decision(
                decision_label="Perform policy checks on originals", choice_value="None"
            )
            self.set_processing_config_decision(
                decision_label="Perform policy checks on preservation derivatives",
                choice_value="None",
            )
            self.set_processing_config_decision(
                decision_label="Assign UUIDs to directories", choice_value="None"
            )
            self.set_processing_config_decision(
                decision_label="Bind PIDs", choice_value="None"
            )
            self.set_processing_config_decision(
                decision_label="Document empty directories", choice_value="None"
            )
        if self.vn in ("1.8",):
            self.set_processing_config_decision(
                decision_label="Generate thumbnails", choice_value="No"
            )

        self.save_default_processing_config()

    # ==========================================================================
    # New Installation
    # ==========================================================================

    def setup_new_install(self):
        """This AM instance has just been created. We need to create the first
        user and register it with its storage service.
        """
        ss_api_key = self.ss_api_key
        self.create_first_user()
        self.wait_for_presence("#id_storage_service_apikey", 100)
        self.driver.find_element_by_id("id_storage_service_apikey").send_keys(
            ss_api_key
        )
        self.driver.find_element_by_css_selector(
            c.varvn("SELECTOR_DFLT_SS_REG", self.vn)
        ).click()

    def create_first_user(self):
        """Create a test user via the /installer/welcome/ page interface."""
        self.driver.get(self.get_installer_welcome_url())
        self.wait_for_presence("#id_org_name")
        self.driver.find_element_by_id("id_org_name").send_keys(c.DEFAULT_AM_USERNAME)
        self.driver.find_element_by_id("id_org_identifier").send_keys(
            c.DEFAULT_AM_USERNAME
        )
        self.driver.find_element_by_id("id_username").send_keys(c.DEFAULT_AM_USERNAME)
        self.driver.find_element_by_id("id_first_name").send_keys(c.DEFAULT_AM_USERNAME)
        self.driver.find_element_by_id("id_last_name").send_keys(c.DEFAULT_AM_USERNAME)
        self.driver.find_element_by_id("id_email").send_keys("test@gmail.com")
        self.driver.find_element_by_id("id_password1").send_keys(c.DEFAULT_AM_PASSWORD)
        self.driver.find_element_by_id("id_password2").send_keys(c.DEFAULT_AM_PASSWORD)
        self.driver.find_element_by_tag_name("button").click()
        continue_button_selector = "input[value=Continue]"
        self.wait_for_presence(continue_button_selector, 100)
        continue_button_el = self.driver.find_element_by_css_selector(
            continue_button_selector
        )
        continue_button_el.click()


def _get_decision_id_from_label(decision_label):
    decision_id = c.PC_DECISION2ID.get(decision_label)
    if decision_id is None:
        for label, id_ in c.PC_DECISION2ID.items():
            if label.lower().startswith(decision_label.lower()):
                decision_id = id_
                break
    if decision_id is None:
        for label, id_ in c.PC_DECISION2ID.items():
            if decision_label.lower() in label.lower():
                decision_id = id_
                break
    if decision_id is None:
        raise ArchivematicaBrowserAbilityError(
            "Unable to determine a decision id given input parameters"
        )
    return decision_id
