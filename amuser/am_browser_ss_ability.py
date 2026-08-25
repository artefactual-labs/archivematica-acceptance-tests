"""Archivematica Browser Storage Service Ability."""

import logging
import pprint
import re

from . import base
from . import playwright_ability
from . import utils

logger = logging.getLogger("amuser.ss")


GPG_KEYIDS_TO_IMPORT = {
    "AAC5E07B370A2D9A": "aadams-passphraseless.key",
    "0F86C799E5DEDE22": "bbingo-passphrased.key",
}


class ArchivematicaBrowserStorageServiceAbilityError(base.ArchivematicaUserError):
    pass


class ArchivematicaBrowserStorageServiceAbility(
    playwright_ability.ArchivematicaPlaywrightAbility
):
    """Interact with the Archivematica Storage Service UI."""

    SS_TABLE_LAYOUT_SELECTORS = {
        "search_input": (
            ".ss-table-search-input",
            "#DataTables_Table_0_filter input",
        ),
        "table": ("table.ss-table-grid", "table#DataTables_Table_0"),
    }

    def _first_ss_present_locator(self, selectors):
        for selector in selectors:
            locator = self.page.locator(selector)
            if locator.count():
                return locator.first
        return None

    def _find_ss_table_search_input(self):
        return self._first_ss_present_locator(
            self.SS_TABLE_LAYOUT_SELECTORS["search_input"]
        )

    def _find_ss_table(self):
        return self._first_ss_present_locator(self.SS_TABLE_LAYOUT_SELECTORS["table"])

    def _search_ss_table(self, search_term):
        search = self._find_ss_table_search_input()
        if not search:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                "Unable to locate Storage Service table search input"
            )
        search.fill(search_term)
        processing = self.page.locator("#DataTables_Table_0_processing")
        if processing.count():
            processing.wait_for(state="hidden")
        if self.page.locator("table.ss-table-grid").count():
            self.wait_for_table_filter(
                "table.ss-table-grid", search_term, ".ss-table-cell--empty"
            )
            return
        self.wait_for_table_filter("table#DataTables_Table_0", search_term)

    def _get_ss_table_data_rows(self):
        table = self._find_ss_table()
        if not table:
            return []
        rows = []
        for row in table.locator("tbody tr").all():
            cells = row.locator("td")
            if not cells.count():
                continue
            row_text = row.inner_text().strip()
            if cells.count() == 1 and (
                "No matching records found" in row_text
                or row_text.startswith("No ")
                or row_text == "Loading data from server"
            ):
                continue
            rows.append(row)
        return rows

    def approve_aip_delete_request(self, aip_uuid):
        """Approve an AIP deletion request through the Storage Service."""
        self.navigate(self.get_ss_package_delete_request_url())
        self._search_ss_table(aip_uuid)
        matching_rows = [
            row
            for row in self._get_ss_table_data_rows()
            if row.locator("td").count() == 7
        ]
        if len(matching_rows) != 1:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                f"Expected one delete request for AIP {aip_uuid}, found "
                f"{len(matching_rows)}"
            )
        row = matching_rows[0]
        row.locator("textarea").fill("Cuz wanna")
        for control in row.locator(
            'input[name="approve"], button, input[type="submit"]'
        ).all():
            label = (control.get_attribute("value") or control.inner_text()).strip()
            if label.casefold() == "approve":
                control.click()
                break
        else:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                "Unable to find approve control in package delete request row"
            )
        assert self.page.locator("div.alert-success").inner_text().strip() == (
            "Request approved: Package deleted successfully."
        )

    def search_for_aip_in_storage_service(self, aip_uuid):
        """Return package table rows matching an AIP UUID."""
        self.navigate(self.get_packages_url())
        self._search_ss_table(aip_uuid)
        table = self._find_ss_table()
        if not table:
            return []
        keys = [
            heading.inner_text().strip().lower().replace(" ", "_")
            for heading in table.locator("thead th").all()
        ]
        result = []
        for row in self._get_ss_table_data_rows():
            cells = row.locator("td").all()
            if len(cells) != len(keys):
                continue
            result.append(
                {
                    keys[index]: " ".join(cell.inner_text().strip().split())
                    for index, cell in enumerate(cells)
                }
            )
        return result

    def ensure_ss_space_exists(self, attributes):
        """Return an equivalent space UUID, creating the space if needed."""
        matching_space = self.search_for_ss_space(attributes)
        if matching_space:
            logger.info("matching space:\n%s", pprint.pformat(matching_space))
            return matching_space["uuid"]
        return self.create_ss_space(attributes)

    def search_for_ss_space(self, attributes):
        """Return the first Storage Service space matching all attributes."""
        for existing_space in self.get_existing_spaces():
            if all(
                existing_space.get(key.lower()) == value
                for key, value in attributes.items()
            ):
                return existing_space
        logger.info("No SS space matching attributes %s", pprint.pformat(attributes))
        return None

    def _fill_labeled_form(self, containers, attributes, choose_pipeline=False):
        for container in containers:
            for label in container.locator("p label").all():
                label_text = label.inner_text().strip().lower().replace(":", "")
                input_id = label.get_attribute("for")
                if not input_id:
                    continue
                control = self.page.locator(f'[id="{input_id}"]')
                for key, value in attributes.items():
                    if key.lower() != label_text:
                        continue
                    tag_name = control.evaluate(
                        "element => element.tagName.toLowerCase()"
                    )
                    if tag_name == "select":
                        control.select_option(label=value)
                    else:
                        control.fill(str(value))
                if choose_pipeline and label_text == "pipeline":
                    control.select_option(index=0)

    def create_ss_space(self, attributes):
        """Create a Storage Service space."""
        if attributes.get("Access protocol") == "GPG encryption on Local Filesystem":
            self.navigate(self.get_gpg_keys_url())
            if (
                attributes.get("GnuPG Private Key")
                == "Archivematica Storage Service GPG Key"
            ):
                key_ids = [
                    anchor.inner_text()
                    for anchor in self.page.locator("tbody tr td:first-child a").all()
                    if anchor.inner_text() not in GPG_KEYIDS_TO_IMPORT
                ]
                assert key_ids
                attributes["GnuPG Private Key"] = key_ids[0]
        self.navigate(self.get_spaces_create_url())
        form = self.page.locator('form[action="/spaces/create/"]')
        protocol = self.page.locator("#protocol_form")
        self._fill_labeled_form((form, protocol), attributes)
        self.page.locator("input[type=submit]").click()
        success = self.page.locator("div.alert-success")
        success.wait_for(
            state="visible", timeout=self._milliseconds(self.nihilistic_wait)
        )
        assert success.inner_text().strip() == "Space saved."
        return (
            self.page.locator("h1")
            .inner_text()
            .strip()
            .split()[0]
            .replace('"', "")
            .replace(":", "")
        )

    def create_ss_location(self, space_uuid, attributes):
        """Create a Storage Service location in a space."""
        self.navigate(self.get_locations_create_url(space_uuid))
        form = self.page.locator(
            f'form[action="/spaces/{space_uuid}/location_create/"]'
        )
        self._fill_labeled_form((form,), attributes, choose_pipeline=True)
        self.page.locator("input[type=submit]").click()
        return (
            self.page.locator("h1")
            .inner_text()
            .strip()
            .split()[0]
            .replace('"', "")
            .replace(":", "")
        )

    @staticmethod
    def _parse_definition_list(definition_list, ignored_values=()):
        result = {}
        last_key = None
        for element in definition_list.locator("dt, dd").all():
            text = element.inner_text().strip()
            tag_name = element.evaluate("node => node.tagName.toLowerCase()")
            if tag_name == "dt":
                last_key = text.lower()
            elif text not in ignored_values:
                result[last_key] = text
        return result

    def get_existing_spaces(self):
        """Return summaries of all existing Storage Service spaces."""
        self.navigate(self.get_spaces_url())
        space_urls = [
            link.evaluate("element => element.href")
            for link in self.page.get_by_role(
                "link", name="View Details and Locations", exact=True
            ).all()
        ]
        existing_spaces = []
        for space_url in filter(None, space_urls):
            self.navigate(space_url)
            space_uuid = space_url.rstrip("/").split("/")[-1]
            space = {"uuid": space_uuid}
            space.update(
                self._parse_definition_list(
                    self.page.locator("div.space dl"), ignored_values=("Actions",)
                )
            )
            existing_spaces.append(space)
        return existing_spaces

    def get_existing_locations(self, space_uuid):
        """Return summaries of all locations in a Storage Service space."""
        self.navigate(self.get_space_url(space_uuid))
        location_uuids = [
            row.locator("td:nth-child(5)").inner_text().strip()
            for row in self.page.locator("tbody tr").all()
        ]
        existing_locations = []
        for location_uuid in location_uuids:
            self.navigate(self.get_location_url(location_uuid))
            location = {"uuid": location_uuid}
            location.update(
                self._parse_definition_list(
                    self.page.locator("div.location dl"),
                    ignored_values=("Space", "Actions"),
                )
            )
            existing_locations.append(location)
        return existing_locations

    def ensure_ss_location_exists(self, space_uuid, attributes):
        """Return an equivalent location UUID, creating it if needed."""
        for location in self.get_existing_locations(space_uuid):
            if all(
                location.get(key.lower()) == value for key, value in attributes.items()
            ):
                return location["uuid"]
        return self.create_ss_location(space_uuid, attributes)

    def _default_aip_storage_replicators(self):
        """Open the default AIP location editor and return its replicator field."""
        self.navigate(self.get_locations_url())
        self._search_ss_table("Store AIP in standard Archivematica Directory")
        rows = [
            row
            for row in self._get_ss_table_data_rows()
            if row.get_by_role("link", name="Edit", exact=True).count()
            and "store aip in standard archivematica directory"
            in row.inner_text().lower()
        ]
        unencrypted_rows = [
            row for row in rows if "encrypted" not in row.inner_text().lower()
        ]
        if unencrypted_rows:
            rows = unencrypted_rows
        if len(rows) != 1:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                "Unable to find a unique default AIP storage location"
            )
        rows[0].get_by_role("link", name="Edit", exact=True).click()
        replicators = self.page.locator("select#id_replicators")
        replicators.wait_for(state="visible")
        return replicators

    def add_replicator_to_default_aip_stor_loc(self, replicator_location_uuid):
        """Add a replicator and return the previous replicator field values."""
        replicators = self._default_aip_storage_replicators()
        previous_values = replicators.locator("option:checked").evaluate_all(
            "options => options.map(option => option.value)"
        )
        for option in replicators.locator("option").all():
            label = option.inner_text()
            if replicator_location_uuid in label:
                selected_values = [*previous_values, option.get_attribute("value")]
                replicators.select_option(list(dict.fromkeys(selected_values)))
                self.page.locator("input[type=submit]").click()
                return previous_values
        raise ArchivematicaBrowserStorageServiceAbilityError(
            f"Unable to find replicator location {replicator_location_uuid}"
        )

    def set_default_aip_storage_replicators(self, replicator_values):
        """Replace the default AIP location's replicators with saved values."""
        replicators = self._default_aip_storage_replicators()
        available_values = set(
            replicators.locator("option").evaluate_all(
                "options => options.map(option => option.value)"
            )
        )
        missing_values = set(replicator_values) - available_values
        if missing_values:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                f"Unable to restore replicator locations {sorted(missing_values)}"
            )
        replicators.select_option(replicator_values)
        self.page.locator("input[type=submit]").click()

    def import_gpg_key(self, key_path):
        """Import a GPG private key and return the resulting alert text."""
        self.navigate(self.get_import_gpg_key_url())
        with open(key_path) as key_input:
            self.page.locator("#id_ascii_armor").fill(key_input.read())
        self.page.locator("input[type=submit]").click()
        alert = self.page.locator("div.alert")
        alert.wait_for(state="visible", timeout=self._milliseconds(20))
        return alert.inner_text().strip()

    def get_gpg_key_search_matches(self, search_string):
        """Return fingerprints for GPG keys matching a search string."""
        self.navigate(self.get_gpg_keys_url())
        self._search_ss_table(search_string)
        fingerprints = []
        for row in self._get_ss_table_data_rows():
            cells = row.locator("td")
            if cells.count() > 1:
                fingerprints.append(cells.nth(1).inner_text().strip())
        return fingerprints

    def delete_gpg_key(self, key_name):
        """Delete the uniquely matching GPG key."""
        self.navigate(self.get_gpg_keys_url())
        self._search_ss_table(key_name)
        matches = self._get_ss_table_data_rows()
        assert len(matches) == 1, (
            f'Unable to delete GPG key "{key_name}": found {len(matches)} matches'
        )
        delete_link = matches[0].get_by_role("link", name="Delete", exact=True)
        if not delete_link.count():
            raise ArchivematicaBrowserStorageServiceAbilityError(
                f'Unable to locate Delete action for key "{key_name}"'
            )
        delete_link.click()
        delete_control = self.page.locator('input[value="Delete"]')
        if not delete_control.count():
            delete_control = self.page.get_by_role("button", name="Delete", exact=True)
        if not delete_control.count():
            error = self.page.locator("div.alert-error")
            return False, error.inner_text().strip()
        delete_control.first.click()
        alert = self.page.locator("div.alert-success, div.alert-error")
        alert.first.wait_for(state="visible")
        class_name = alert.first.get_attribute("class") or ""
        return "alert-success" in class_name, alert.first.inner_text().strip()

    def create_new_gpg_key(self):
        """Create a GPG key with a unique name."""
        self.navigate(self.get_create_gpg_key_url())
        new_key_name = f"GPGKey {utils.unixtimestamp()}"
        new_key_email = f"{new_key_name.lower().replace(' ', '')}@example.com"
        self.page.locator("#id_name_real").fill(new_key_name)
        self.page.locator("#id_name_email").fill(new_key_email)
        self.page.locator("input[type=submit]").click()
        success = self.page.locator("div.alert-success").filter(
            has_text=re.compile(r"New key \S+ created\.")
        )
        success.first.wait_for(
            state="visible", timeout=self._milliseconds(self.nihilistic_wait)
        )
        new_key_fingerprint = success.first.inner_text().split()[2]
        new_key_id = self.page.locator("dd").nth(1).inner_text()
        return new_key_name, new_key_email, new_key_fingerprint, new_key_id

    def change_encrypted_space_key(self, space_uuid, new_key_repr=None):
        """Change the key associated with an encrypted space."""
        self.navigate(self.get_space_edit_url(space_uuid))
        key_select = self.page.locator("#id_protocol-key")
        if new_key_repr:
            key_select.select_option(label=new_key_repr)
        else:
            current_label = key_select.locator("option:checked").inner_text()
            for option in key_select.locator("option").all():
                label = option.inner_text()
                if label != current_label:
                    key_select.select_option(label=label)
                    break
        self.page.locator("input[type=submit]").click()
        success = self.page.locator("div.alert-success")
        success.wait_for(
            state="visible", timeout=self._milliseconds(self.nihilistic_wait)
        )
        assert success.inner_text().strip() == "Space saved."
