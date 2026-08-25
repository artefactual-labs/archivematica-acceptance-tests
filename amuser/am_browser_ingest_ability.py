"""Archivematica Ingest Tab Ability."""

import logging
import os
import tempfile

import tenacity
from amclient import AMClient
from lxml import etree
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from . import base
from . import constants as c
from . import playwright_ability
from . import utils


class ArchivematicaBrowserMETSAbilityError(base.ArchivematicaUserError):
    pass


logger = logging.getLogger("amuser.ingest")


class ArchivematicaBrowserIngestAbility(
    playwright_ability.ArchivematicaPlaywrightAbility
):
    """Interact with Archivematica's Ingest tab."""

    def remove_all_ingests(self):
        """Remove all ingests in the Ingest tab."""
        url = self.get_ingest_url()
        self.navigate(url)
        try:
            self.wait_for_presence(c.SELECTOR_TRANSFER_DIV, 20)
        except PlaywrightTimeoutError:
            return
        while top_transfer := self.get_top_transfer():
            self.remove_top_transfer(top_transfer)

    def get_sip_uuid(self, transfer_name):
        logger.info("Getting SIP UUID from transfer name %s", transfer_name)
        self.navigate(self.get_ingest_url(), reload=True)
        sip_uuid, _, _ = self.wait_for_transfer_to_appear(transfer_name)
        logger.info("Got SIP UUID %s", sip_uuid)
        return sip_uuid

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(20),
        wait=tenacity.wait_exponential(
            multiplier=c.MICRO_WAIT,
            max=c.OPTIMISTIC_WAIT,
        ),
    )
    def get_mets_via_api(self, transfer_name, sip_uuid=None, parse_xml=True):
        """Return METS once stored in an AIP."""
        if not sip_uuid:
            sip_uuid = self.get_sip_uuid(transfer_name)
        absolute_transfer_name = f"{transfer_name}-{sip_uuid}"
        mets_name = f"METS.{sip_uuid}.xml"
        mets_path = f"{absolute_transfer_name}/data/{mets_name}"
        mets_tmp_dir = tempfile.mkdtemp()
        mets_tmp_file = os.path.join(mets_tmp_dir, mets_name)
        AMClient(
            ss_api_key=self._ss_api_key,
            ss_user_name=self.ss_username,
            ss_url=self.ss_url.rstrip("/"),
            package_uuid=sip_uuid,
            relative_path=mets_path,
            saveas_filename=mets_tmp_file,
        ).extract_file()
        with open(mets_tmp_file) as mets_file:
            mets = mets_file.read()
        os.unlink(mets_tmp_file)
        if parse_xml:
            return etree.fromstring(mets.encode("utf8"))
        return mets

    def get_mets(self, transfer_name, sip_uuid=None, parse_xml=True):
        """Return the METS XML from Archivematica's Review AIP interface."""
        if not sip_uuid:
            sip_uuid = self.get_sip_uuid(transfer_name)
        self.navigate(self.get_ingest_url())
        ms_name = utils.normalize_ms_name("Store AIP (review)", self.vn)
        self.expose_job(ms_name, sip_uuid, "ingest")
        self.navigate(self.get_aip_preview_url(sip_uuid).format(self.am_url, sip_uuid))
        mets_path = f"storeAIP/{transfer_name}-{sip_uuid}/METS.{sip_uuid}.xml"
        with self.page.expect_popup(
            timeout=self._milliseconds(self.apathetic_wait)
        ) as popup_info:
            self.navigate_to_aip_directory_and_click(mets_path)
        popup = popup_info.value
        try:
            try:
                expect(popup).not_to_have_url(
                    "about:blank", timeout=self._milliseconds(self.nihilistic_wait)
                )
            except AssertionError as exc:
                msg = "Timed out waiting for the METS file to load."
                logger.warning(msg)
                raise ArchivematicaBrowserMETSAbilityError(msg) from exc
            mets = popup.content()
        finally:
            popup.close()
        if parse_xml:
            return etree.fromstring(mets.encode("utf8"))
        return mets

    def navigate_to_aip_directory_and_click(self, path):
        """Open each directory in ``path`` and click the terminal file."""
        self._navigate_to_aip_directory_and_click(path)

    def _navigate_to_aip_directory_and_click(self, path):
        self.cwd = ["explorer_var_archivematica_sharedDirectory_watchedDirectories"]
        path_parts = path.strip("/").split("/")
        if path_parts[-1].startswith("METS."):
            path_parts[-1] = f"METS__{path_parts[-1][5:]}"
        self.page.locator("#explorer").wait_for(
            state="attached", timeout=self._milliseconds(self.medium_wait)
        )
        for index, folder in enumerate(path_parts):
            self.cwd.append(folder)
            folder_id = "_".join(self.cwd)
            if index == len(path_parts) - 1:
                self.click_file_old_browser(folder_id)
            else:
                self.click_folder_old_browser(folder_id)

    def add_dummy_metadata(self, sip_uuid):
        self.navigate(self.get_ingest_url())
        self.page.locator(f"#sip-row-{sip_uuid}").locator("a.btn_show_metadata").click()
        self.navigate(self.get_metadata_add_url(sip_uuid))
        for attr in self.metadata_attrs:
            self.page.locator(f"#id_{attr}").fill(self.dummy_val)
        submit = self.page.locator('input[value="Create"], input[value="Save"]')
        submit.first.click()

    def parse_normalization_report(self, sip_uuid):
        """Open and parse the normalization report into a list of mappings."""
        self.navigate(self.get_ingest_url(), reload=True)
        ms_name = utils.normalize_ms_name("Approve normalization (review)", self.vn)
        self.expose_job(ms_name, sip_uuid, "sip")
        self.navigate(self.get_normalization_report_url(sip_uuid), reload=True)
        table = self.page.locator("table")
        table.wait_for(state="visible")
        keys = [
            heading.inner_text().strip().lower().replace(" ", "_")
            for heading in table.locator("thead tr th").all()
        ]
        report = []
        for table_row in table.locator("tbody tr").all():
            row = {}
            for index, cell in enumerate(table_row.locator("td").all()):
                row[keys[index]] = cell.inner_text()
            report.append(row)
        return report
