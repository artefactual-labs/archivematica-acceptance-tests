"""Archivematica Browser Ability

This module contains the ``ArchivematicaBrowserAbility`` class, which encodes
the ability of an Archivematica user to use Playwright to interact with
Archivematica and the Storage Service.
"""

import logging
import re

import requests
from playwright.sync_api import expect

from . import am_browser_auth_ability as auth_abl
from . import am_browser_preservation_planning_ability as pres_plan_abl
from . import am_browser_ss_ability as ss_abl
from . import am_browser_transfer_ingest_ability as tra_ing_abl
from . import base
from . import constants as c

logger = logging.getLogger("amuser.browser")

PROCESSING_CONFIG_LOAD_ERROR = "Unable to load processing configuration page."
PROCESSING_CONFIG_LOAD_ATTEMPTS = 3


class ArchivematicaBrowserAbilityError(base.ArchivematicaUserError):
    pass


class ArchivematicaBrowserAbility(
    auth_abl.ArchivematicaBrowserAuthenticationAbility,
    tra_ing_abl.ArchivematicaBrowserTransferIngestAbility,
    ss_abl.ArchivematicaBrowserStorageServiceAbility,
    pres_plan_abl.ArchivematicaBrowserPreservationPlanningAbility,
):
    """Use Playwright to interact with live Archivematica services."""

    @property
    def ss_api_key(self):
        if not self._ss_api_key:
            self.page.goto(self.get_ss_login_url())
            self.page.locator("#id_username").fill(self.ss_username)
            self.page.locator("#id_password").fill(self.ss_password)
            self.page.locator(c.varvn("SELECTOR_SS_LOGIN_BUTTON", self.vn)).click()
            self.page.goto(self.get_default_ss_user_edit_url())
            code = self.page.locator("code")
            code.wait_for(state="attached", timeout=self._milliseconds(20))
            self._ss_api_key = code.inner_text().strip()
        return self._ss_api_key

    def get_displayed_tabs(self):
        tabs = [
            item.inner_text().strip().split("\n")[0]
            for item in self.page.locator("ul.navbar-nav li").all()
        ]
        return list(filter(None, tabs))

    def assert_sip_arrange_pane_not_displayed(self):
        for selector in ("form#search_form", "div#originals", "div#arrange"):
            assert self.page.locator(selector).count() == 0
        assert self.page.locator("div#sip-container").count()

    # ==========================================================================
    # Archival Storage Tab
    # ==========================================================================

    def _submit_archival_storage_vue_search(self, aip_uuid):
        """Submit a Vue archival-storage search and await its response."""
        with self.page.expect_response(
            lambda response: (
                "/archival-storage/search/" in response.url and aip_uuid in response.url
            ),
            timeout=self._milliseconds(self.apathetic_wait),
        ):
            self.page.locator("#search_form button[type='submit']").click()
        live_status = self.page.locator("p.sr-only[aria-live='polite']")
        expect(live_status).not_to_have_text(
            "Loading results", timeout=self._milliseconds(self.pessimistic_wait)
        )

    def _search_archival_storage_vue(self, aip_uuid: str) -> bool | None:
        """Search Archival Storage through the Vue interface.

        This method returns ``True`` when the AIP is visible in the Vue table
        results. It returns ``False`` when the Vue search controls exist but no
        match is currently shown. It returns ``None`` when the Vue selectors
        are not present at all, which allows callers to try legacy selectors.
        """
        query_inputs = self.page.locator("#search_form .aip-search-query-input")
        if not query_inputs.count():
            return None

        query_inputs.first.fill(aip_uuid)
        field_select = self.page.locator("#search_form .search-field-select")
        if field_select.locator('option[value="AIPUUID"]').count():
            field_select.select_option(value="AIPUUID")
        else:
            field_select.select_option(label="AIP UUID")
        type_select = self.page.locator("#search_form .search-type-select")
        if type_select.locator('option[value="string"]').count():
            type_select.select_option(value="string")
        else:
            type_select.select_option(label="Phrase")
        self._submit_archival_storage_vue_search(aip_uuid)
        return bool(
            self.page.locator(f'a[href$="/archival-storage/{aip_uuid}/"]').count()
        )

    def _search_archival_storage_legacy(self, aip_uuid: str) -> bool | None:
        """Search Archival Storage through the legacy DataTables interface.

        This method returns ``True`` when the legacy results table shows at
        least one match for the requested AIP UUID. It returns ``False`` when
        the legacy controls exist but the filtered result is empty. It returns
        ``None`` when the legacy controls are missing, which signals that the
        UI likely uses a different layout.
        """
        query_inputs = self.page.locator('input[title="search query"]')
        if not query_inputs.count():
            return None

        query_inputs.first.fill(aip_uuid)
        self.page.locator('select[title="field name"]').select_option(label="AIP UUID")
        self.page.locator('select[title="query type"]').select_option(label="Phrase")
        self.page.locator("#search_submit").click()
        self.wait_for_presence("#archival-storage-entries_info")

        summary = self.page.locator("#archival-storage-entries_info")
        found = summary.inner_text().strip() != "Showing 0 to 0 of 0 entries"
        return found

    def wait_for_aip_in_archival_storage(self, aip_uuid: str) -> None:
        """Wait for the AIP with UUID ``aip_uuid`` to appear in the Archival
        storage tab.
        """
        max_attempts = self.max_search_aip_archival_storage_attempts
        attempts = 0
        while True:
            self.navigate(self.get_archival_storage_url(), reload=True)

            vue_result = self._search_archival_storage_vue(aip_uuid)
            if vue_result is True:
                break

            if vue_result is None:
                legacy_result = self._search_archival_storage_legacy(aip_uuid)
                if legacy_result is True:
                    break
                if legacy_result is None:
                    # As a final compatibility fallback, we probe the direct
                    # AIP detail URL. If that page is reachable, we can treat
                    # the AIP as present in archival storage.
                    self.navigate_to_aip_in_archival_storage(aip_uuid)
                    break

            attempts += 1
            if attempts > max_attempts:
                break
            self.wait(self.optimistic_wait)

    def find_aip_by_transfer_metadata(
        self, aip_uuid, search_phrase, expected_summary_message
    ):
        """Search archival storage by AIP UUID and transfer metadata."""
        expected_match = re.search(
            r"Showing \d+ to \d+ of (\d+) entries", expected_summary_message
        )
        assert expected_match, (
            f"Unexpected expected summary format: {expected_summary_message!r}"
        )
        expected_entries = int(expected_match.group(1))
        self.navigate(self.get_archival_storage_url(), reload=True)

        rows = self.page.locator("#search_form .archival-row")
        if rows.count():
            first_row = rows.first
            first_row.locator("input.aip-search-query-input").fill(aip_uuid)
            first_selects = first_row.locator("select")
            first_selects.nth(0).select_option(value="AIPUUID")
            first_selects.nth(1).select_option(value="string")
            if rows.count() < 2:
                self.page.locator(
                    "#search_form .submit-actions-left button.btn.btn-default"
                ).first.click()
            rows = self.page.locator("#search_form .archival-row")
            rows.nth(1).wait_for(state="attached")
            second_row = rows.last
            second_row.locator("input.aip-search-query-input").fill(
                f'"{search_phrase}"'
            )
            second_selects = second_row.locator("select")
            second_selects.nth(0).select_option(value="and")
            second_selects.nth(1).select_option(value="transferMetadata")
            second_selects.nth(2).select_option(value="string")
            self._submit_archival_storage_vue_search(aip_uuid)
            matching_links = self.page.locator(
                f'a[href$="/archival-storage/{aip_uuid}/"]'
            )
            unique_urls = {
                href
                for href in matching_links.evaluate_all(
                    "links => links.map(link => link.href)"
                )
                if href
            }
            assert len(unique_urls) == expected_entries, (
                f"Search phrase {search_phrase!r}: expected {expected_entries} "
                f"entries for {aip_uuid}, got {len(unique_urls)}"
            )
            return True

        queries = self.page.locator('input[title="search query"]')
        queries.first.fill(aip_uuid)
        self.page.locator('select[title="field name"]').first.select_option(
            label="AIP UUID"
        )
        self.page.locator('select[title="query type"]').first.select_option(
            label="Phrase"
        )
        self.page.get_by_role("link", name="Add new", exact=True).click()
        self.page.locator("select.search_op_selector").select_option(label="and")
        self.page.locator('input[title="search query"]').last.fill(f'"{search_phrase}"')
        self.page.locator('select[title="field name"]').last.select_option(
            label="Transfer metadata"
        )
        self.page.locator('select[title="query type"]').last.select_option(
            label="Phrase"
        )
        self.page.locator("#search_submit").click()
        self.wait_for_presence("#archival-storage-entries tbody tr")
        summary = self.page.locator("#archival-storage-entries_info").inner_text()
        assert summary.strip() == expected_summary_message, (
            f"Search phrase {search_phrase!r}: expected "
            f"{expected_summary_message!r}, got {summary.strip()!r}"
        )
        return True

    def request_aip_delete(self, aip_uuid):
        """Request the deletion of the AIP with UUID ``aip_uuid`` using the
        dashboard GUI.
        """
        self.navigate_to_aip_in_archival_storage(aip_uuid)
        delete_tab_selector = 'a[href="#tab-delete"]'
        self.wait_for_presence(delete_tab_selector, timeout=self.apathetic_wait)
        delete_uuid = self.page.locator("#id_delete-uuid")
        if not delete_uuid.is_visible():
            self.page.locator(delete_tab_selector).click()
            delete_uuid.wait_for(state="visible")
        delete_uuid.fill(aip_uuid)
        self.page.locator("#id_delete-reason").fill("Cuz wanna")
        self.page.locator('button[name="submit-delete-form"]').click()
        self.wait_for_visibility("div.alert-info")
        alert_text = self.page.locator("div.alert-info").inner_text().strip()
        assert alert_text == "Delete request created successfully."

    def navigate_to_aip_in_archival_storage(self, aip_uuid):
        url = self.get_aip_in_archival_storage_url(aip_uuid)
        max_attempts = self.max_navigate_aip_archival_storage_attempts
        attempt = 0
        s = requests.session()
        for cookie in self.browser_context.cookies():
            s.cookies.update({cookie["name"]: cookie["value"]})
        while True:
            if attempt > max_attempts:
                raise ArchivematicaBrowserAbilityError(f"Unable to navigate to {url}")
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
            self.wait(self.optimistic_wait)
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
                f"Unable to initiate a reingest of type {reingest_type} on AIP"
                f" {aip_uuid}"
            )
        type_input = self.page.locator(type_selector)
        if not type_input.is_visible():
            self.page.locator(reingest_tab_selector).click()
            type_input.wait_for(state="visible")
        type_input.check()
        self.page.locator("button[name=submit-reingest-form]").click()
        self.wait_for_visibility("div.alert-success")
        alert_text = self.page.locator("div.alert-success").inner_text().strip()
        assert alert_text.startswith(f"Package {aip_uuid} sent to pipeline")
        assert alert_text.endswith("for re-ingest")

    # ==========================================================================
    # Administration Tab
    # ==========================================================================

    def upload_policy(self, policy_path):
        self.navigate_to_policies()
        self.page.locator("input[name=file]").set_input_files(policy_path)
        self.page.locator("input[type=submit]").click()

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
            control = self.page.locator(f"#id_{key}")
            tag_name = control.evaluate("element => element.tagName.toLowerCase()")
            if tag_name == "select":
                control.select_option(label=val)
            elif control.get_attribute("type") == "checkbox":
                control.set_checked(bool(val))
            else:
                control.fill(str(val))
        self.page.locator("input[type=submit]").click()
        self.wait_for_visibility("div.alert-info")
        assert self.page.locator(".alert-info").inner_text().strip() == "Saved.", (
            "Unable to confirm saving of Handle configuration"
        )

    def get_es_indexing_config_text(self):
        self.navigate(self.get_admin_general_url())
        indexing_configuration = self.page.locator("p.es-indexing-configuration")
        if not indexing_configuration.count():
            return None
        return indexing_configuration.inner_text()

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
        if self.page.url != edit_default_processing_config_url:
            self.navigate(edit_default_processing_config_url)
        self.page.locator('input[value="Save"]').click()

    def _get_processing_config_decision(self, decision_id):
        """Return a decision field, retrying explicit configuration load errors."""
        edit_url = self.get_edit_default_processing_config_url()
        for attempt in range(1, PROCESSING_CONFIG_LOAD_ATTEMPTS + 1):
            decision = self.page.locator(f'[id="{decision_id}"]')
            if decision.count():
                return decision
            load_error = self.page.get_by_text(PROCESSING_CONFIG_LOAD_ERROR, exact=True)
            if not load_error.count() or attempt == PROCESSING_CONFIG_LOAD_ATTEMPTS:
                decision.wait_for(state="attached")
                return decision
            logger.warning(
                "Retrying processing configuration page after load error (%d/%d)",
                attempt,
                PROCESSING_CONFIG_LOAD_ATTEMPTS,
            )
            self.page.goto(edit_url)

        raise AssertionError("Unreachable processing configuration retry state")

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
        if self.page.url != edit_default_processing_config_url:
            self.navigate(edit_default_processing_config_url)
        # Get a decision_id value, something of the form 'id_<UUID>'
        if decision_id is None:
            decision_id = _get_decision_id_from_label(decision_label)
        else:
            if not decision_id.startswith("id_"):
                decision_id = "id_" + decision_id
        decision = self._get_processing_config_decision(decision_id)
        options = []
        if decision.evaluate("element => element.tagName.toLowerCase()") == "select":
            options = [
                option.inner_text().strip()
                for option in decision.locator("option").all()
            ]
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
        if self.page.url != edit_default_processing_config_url:
            self.navigate(edit_default_processing_config_url)
        # Get a decision_id value, something of the form 'id_<UUID>'
        if decision_id is None:
            decision_id = _get_decision_id_from_label(decision_label)
        else:
            if not decision_id.startswith("id_"):
                decision_id = "id_" + decision_id
        decision = self._get_processing_config_decision(decision_id)
        if decision.evaluate("element => element.tagName.toLowerCase()") == "select":
            if choice_value_attr is not None:
                decision.select_option(value=choice_value_attr)
            elif choice_index is not None:
                decision.select_option(index=choice_index)
            else:
                decision.select_option(label=choice_value)
        else:
            decision.fill(choice_value)

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
        self.page.locator("#id_storage_service_apikey").fill(ss_api_key)
        self.page.locator(c.varvn("SELECTOR_DFLT_SS_REG", self.vn)).click()

    def create_first_user(self):
        """Create a test user via the /installer/welcome/ page interface."""
        self.page.goto(self.get_installer_welcome_url())
        self.wait_for_presence("#id_org_name")
        values = {
            "id_org_name": c.DEFAULT_AM_USERNAME,
            "id_org_identifier": c.DEFAULT_AM_USERNAME,
            "id_username": c.DEFAULT_AM_USERNAME,
            "id_first_name": c.DEFAULT_AM_USERNAME,
            "id_last_name": c.DEFAULT_AM_USERNAME,
            "id_email": "test@gmail.com",
            "id_password1": c.DEFAULT_AM_PASSWORD,
            "id_password2": c.DEFAULT_AM_PASSWORD,
        }
        for input_id, value in values.items():
            self.page.locator(f"#{input_id}").fill(value)
        self.page.locator("button").first.click()
        continue_button_selector = 'input[value="Continue"]'
        self.wait_for_presence(continue_button_selector, 100)
        self.page.locator(continue_button_selector).click()


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
