"""Archivematica Ingest Tab Ability"""

import logging
import time

from lxml import etree
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    MoveTargetOutOfBoundsException,
    NoSuchElementException,
    TimeoutException,
)

from . import constants as c
from . import utils
from . import selenium_ability


logger = logging.getLogger('amuser.ingest')


class ArchivematicaBrowserIngestAbility(
        selenium_ability.ArchivematicaSeleniumAbility):
    """Archivematica Browser Ingest Tab Ability."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.click_aip_directory_tries = 0

    def remove_all_ingests(self):
        """Remove all ingests in the Ingest tab."""
        url = self.get_ingest_url()
        self.driver.get(url)
        if self.driver.current_url != url:
            self.login()
        self.driver.get(url)
        self.wait_for_presence(c.SELECTOR_TRANSFER_DIV, 20)
        while True:
            top_transfer_elem = self.get_top_transfer()
            if not top_transfer_elem:
                break
            self.remove_top_transfer(top_transfer_elem)

    def get_sip_uuid(self, transfer_name):
        logger.info('Getting SIP UUID from transfer name %s', transfer_name)
        self.driver.quit()
        self.driver = self.get_driver()
        ingest_url = self.get_ingest_url()
        self.driver.get(ingest_url)
        if self.driver.current_url != ingest_url:
            self.login()
        self.driver.get(ingest_url)
        sip_uuid, _, _ = (
            self.wait_for_transfer_to_appear(transfer_name))
        logger.info('Got SIP UUID %s', sip_uuid)
        return sip_uuid

    def get_mets(self, transfer_name, sip_uuid=None, parse_xml=True):
        """Return the METS file XML as an lxml instance or as a string if
        ``parse_xml`` is set to ``False``.

        WARNING: this only works if the processingMCP.xml config file is set to
        *not* store the AIP.
        """
        if not sip_uuid:
            sip_uuid = self.get_sip_uuid(transfer_name)
        ingest_url = self.get_ingest_url()
        self.navigate(ingest_url)
        # Wait for the "Store AIP" micro-service.
        ms_name = utils.normalize_ms_name('Store AIP (review)', self.vn)
        self.expose_job(ms_name, sip_uuid, 'ingest')
        aip_preview_url = '{}/ingest/preview/aip/{}'.format(
            self.am_url, sip_uuid)
        self.navigate(aip_preview_url)
        mets_path = 'storeAIP/{}-{}/METS.{}.xml'.format(
            transfer_name, sip_uuid, sip_uuid)
        handles_before = self.driver.window_handles
        self.navigate_to_aip_directory_and_click(mets_path)
        self.wait_for_new_window(handles_before)
        original_window_handle = self.driver.window_handles[0]
        new_window_handle = self.driver.window_handles[1]
        self.driver.switch_to.window(new_window_handle)
        while self.driver.current_url.strip() == 'about:blank':
            time.sleep(1)
        mets = self.driver.page_source
        self.driver.switch_to.window(original_window_handle)
        if parse_xml:
            return etree.fromstring(mets.encode('utf8'))
        return mets

    def navigate_to_aip_directory_and_click(self, path):
        """Click on the file at ``path`` in the "Review AIP" interface.
        TODO: non-DRY given
        ``navigate_to_transfer_directory_and_click``--fix if possible.
        """
        try:
            self._navigate_to_aip_directory_and_click(path)
        except (TimeoutException, MoveTargetOutOfBoundsException):
            self.click_aip_directory_tries += 1
            if (self.click_aip_directory_tries >=
                    c.MAX_CLICK_AIP_DIRECTORY_TRIES):
                print('Failed to navigate to aip directory'
                      ' {}'.format(path))
                self.click_aip_directory_tries = 0
                raise
            else:
                self.navigate_to_aip_directory_and_click(path)
        else:
            self.click_aip_directory_tries = 0

    def _navigate_to_aip_directory_and_click(self, path):
        self.cwd = [
            'explorer_var_archivematica_sharedDirectory_watchedDirectories']
        while path.startswith('/'):
            path = path[1:]
        while path.endswith('/'):
            path = path[:-1]
        path_parts = path.split('/')
        if path_parts[-1].startswith('METS.'):
            path_parts[-1] = 'METS__{}'.format(path_parts[-1][5:])
        for i, folder in enumerate(path_parts):
            is_last = False
            if i == len(path_parts) - 1:
                is_last = True
            self.cwd.append(folder)
            folder_id = '_'.join(self.cwd)
            block = WebDriverWait(self.driver, 1)
            block.until(EC.presence_of_element_located(
                (By.ID, 'explorer')))
            if is_last:
                self.click_file_old_browser(folder_id)
                # self.click_file(folder_id)
            else:
                self.click_folder_old_browser(folder_id)
                # self.click_folder(folder_id)

    def add_dummy_metadata(self, sip_uuid):
        self.navigate(self.get_ingest_url())
        self.driver.find_element_by_id('sip-row-{}'.format(sip_uuid))\
            .find_element_by_css_selector('a.btn_show_metadata').click()
        self.navigate(self.get_metadata_add_url(sip_uuid))
        for attr in self.metadata_attrs:
            self.driver.find_element_by_id('id_{}'.format(attr))\
                .send_keys(self.dummy_val)
        try:
            self.driver.find_element_by_css_selector(
                'input[value=Create]').click()
        except NoSuchElementException:
            # Should be a "Create" button but sometimes during development the
            # metadata already exists so it is a "Save" button.
            self.driver.find_element_by_css_selector(
                'input[value=Save]').click()

    def parse_normalization_report(self, sip_uuid):
        """Wait for the "Approve normalization" job to appear and then open the
        normalization report, parse it and return a list of dicts.
        """
        report = []
        self.driver.quit()
        self.driver = self.get_driver()
        url = self.get_ingest_url()
        self.driver.get(url)
        if self.driver.current_url != url:
            self.login()
        self.driver.get(url)
        ms_name = utils.normalize_ms_name('Approve normalization (review)', self.vn)
        self.expose_job(ms_name, sip_uuid, 'sip')
        nrmlztn_rprt_url = self.get_normalization_report_url(sip_uuid)
        self.driver.get(nrmlztn_rprt_url)
        if self.driver.current_url != nrmlztn_rprt_url:
            self.login()
        self.driver.get(nrmlztn_rprt_url)
        self.wait_for_presence('table')
        table_el = self.driver.find_element_by_css_selector('table')
        keys = [td_el.text.strip().lower().replace(' ', '_')
                for td_el in table_el
                .find_element_by_css_selector('thead tr')
                .find_elements_by_css_selector('th')]
        for tr_el in table_el.find_elements_by_css_selector('tbody tr'):
            row = {}
            for index, td_el in enumerate(
                    tr_el.find_elements_by_css_selector('td')):
                row[keys[index]] = td_el.text
            report.append(row)
        return report
