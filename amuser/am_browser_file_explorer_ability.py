"""Archivematica Browser File Explorer Ability"""

import logging
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    MoveTargetOutOfBoundsException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains

from . import constants as c
from . import selenium_ability


logger = logging.getLogger('amuser.fileexplorer')


class ArchivematicaBrowserFileExplorerAbility(
        selenium_ability.ArchivematicaSeleniumAbility):
    """Archivematica Browser File Explorer Ability."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.click_transfer_directory_tries = 0

    def add_transfer_directory(self, path):
        """Navigate to the transfer directory at ``path`` and click its "Add"
        link.
        """
        # Click the "Browse" button, if necessary.
        if not self.driver.find_element_by_css_selector(
                c.SELECTOR_DIV_TRANSFER_SOURCE_BROWSE).is_displayed():
            browse_button_elem = self.driver.find_element_by_css_selector(
                c.SELECTOR_BUTTON_BROWSE_TRANSFER_SOURCES)
            browse_button_elem.click()
        # Wait for the File Explorer modal dialog to open.
        block = WebDriverWait(self.driver, self.pessimistic_wait)
        block.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, c.SELECTOR_DIV_TRANSFER_SOURCE_BROWSE)))
        # Navigate to the leaf directory and click "Add".
        self.navigate_to_transfer_directory_and_click(path)

    def navigate_to_transfer_directory_and_click(self, path):
        """Click on each folder in ``path`` from the root on up, until we
        get to the leaf; then click "Add".
        This method recurses itself up to
        ``self.max_click_transfer_directory_attempts`` times if it fails. This
        may no longer be necessary now that the file browser has been updated.
        """
        try:
            self._navigate_to_transfer_directory_and_click(path)
        except (TimeoutException, MoveTargetOutOfBoundsException):
            self.click_transfer_directory_tries += 1
            if (self.click_transfer_directory_tries >=
                    self.max_click_transfer_directory_attempts):
                logger.warning('Failed to navigate to transfer directory'
                               ' %s', path)
                self.click_transfer_directory_tries = 0
                raise
            else:
                self.navigate_to_transfer_directory_and_click(path)
        else:
            self.click_transfer_directory_tries = 0

    def _navigate_to_transfer_directory_and_click(self, path):
        """Click on each folder icon in ``path`` from the root on up, until we
        get to the terminal folder, in which case we click the folder label and
        then the "Add" button.
        """
        xtrail = []  # holds XPaths matching each folder name.
        path = path.strip('/')
        path_parts = path.split('/')
        for i, folder in enumerate(path_parts):
            logger.info('Clicking on "%s"', folder)
            is_last = False
            if i == len(path_parts) - 1:
                is_last = True
            folder_label_xpath = get_xpath_matches_folder_text(folder)
            if i == 0:
                folder_label_xpath = '//{}'.format(folder_label_xpath)
            xtrail.append(folder_label_xpath)
            # Now the XPath matches folder ONLY if it's in the directory it
            # should be, i.e., this is now an absolute XPath.
            folder_label_xpath = c.XPATH_TREEITEM_NEXT_SIBLING.join(xtrail)
            # Wait until folder is visible.
            block = WebDriverWait(self.driver, self.pessimistic_wait)
            block.until(EC.presence_of_element_located(
                (By.XPATH, folder_label_xpath)))
            if is_last:
                logger.info('Clicking to select folder "%s"', folder)
                # Click target (leaf) folder and then "Add" button.
                folder_el = self.driver.find_element_by_xpath(folder_label_xpath)
                self.click_folder_label(folder_el)
                time.sleep(self.pessimistic_wait)
                self.click_add_button()
                self.driver.execute_script('window.scrollTo(0, 0);')
                logger.info('Clicked to select folder "%s"', folder)
            else:
                # Click ancestor folder's icon to open its contents.
                logger.info('Clicking to open folder "%s"', folder)
                self.click_folder(folder_label_xpath)
                logger.info('Clicked to open folder "%s"', folder)

    def click_add_folder(self, folder_id):
        """Click the "Add" link in the old AM file explorer interface, i.e., to
        add a directory to a transfer.
        """
        block = WebDriverWait(self.driver, 10)
        block.until(EC.presence_of_element_located(
            (By.ID, folder_id)))
        folder_elem = self.driver.find_element_by_id(folder_id)
        hover = ActionChains(self.driver).move_to_element(folder_elem)
        hover.perform()
        time.sleep(self.micro_wait)  # seems to be necessary (! jQuery animations?)
        span_elem = self.driver.find_element_by_css_selector(
            'div#{} span.{}'.format(folder_id,
                                    c.CLASS_ADD_TRANSFER_FOLDER))
        hover = ActionChains(self.driver).move_to_element(span_elem)
        hover.perform()
        span_elem.click()

    def click_file(self, file_id):
        """Click a file in the new an AM file explorer interface, e.g., when
        reviewing an AIP.
        """
        self.click_folder(file_id, True)

    def click_file_old_browser(self, file_id):
        """Click a file in the old AM file explorer interface, e.g., when
        reviewing an AIP.
        """
        self.click_folder_old_browser(file_id, True)

    def click_folder_label(self, folder_el, offset=0):
        logger.info('Attempting to click folder element at offset %s.', offset)
        counter = 0
        try:
            if counter > 10:
                return
            folder_el.click()
            if not self.driver.find_element_by_css_selector(
                    c.SELECTOR_BUTTON_ADD_DIR_TO_TRANSFER).is_enabled():
                logger.info('The Add button has not become clickable.')
                raise WebDriverException('ADD is not clickable')
            logger.info('The Add button has become clickable.')
        except WebDriverException:
            counter += 1
            container_el = self.driver.find_element_by_css_selector(
                '.transfer-tree-container')
            self.driver.execute_script(
                "arguments[0].scrollTop = {}".format(offset), container_el)
            self.click_folder_label(folder_el, offset + 100)

    def click_folder(self, folder_label_xpath, is_file=False, offset=0):
        """Click a folder in the new AM file explorer interface (i.e., the one
        introduced by the merging of dev/integrate-transfer-browser into qa/1.x
        (PR#491).
        :param bool is_file: indicates whether the folder is actually a file,
            which is the case when you're clicking a METS file in the "Review
            AIP" file explorer.
        """
        try:
            block = WebDriverWait(self.driver, 10)
            block.until(EC.presence_of_element_located(
                (By.XPATH, folder_label_xpath)))
            folder_icon_xpath = folder_label2icon_xpath(folder_label_xpath)
            folder_icon_el = self.driver.find_element_by_xpath(folder_icon_xpath)
            folder_icon_el.click()
            folder_children_xpath = folder_label2children_xpath(
                folder_label_xpath)
            block = WebDriverWait(self.driver, 10)
            block.until(EC.visibility_of_element_located(
                (By.XPATH, folder_children_xpath)))
            # TODO: when clicking a file in the new interface (if ever this is
            # required), we may need different behaviour.
        except WebDriverException:
            container_el = self.driver.find_element_by_css_selector(
                '.transfer-tree-container')
            self.driver.execute_script(
                "arguments[0].scrollTop = {}".format(offset), container_el)
            self.click_folder(folder_label_xpath, is_file, offset + 100)

    def click_folder_old_browser(self, folder_id, is_file=False):
        """Click a folder in the old AM file explorer interface (i.e., the one
        before dev/integrate-transfer-browser.
        :param bool is_file: indicates whether the folder is actually a file,
            which is the case when you're clicking a METS file in the "Review
            AIP" file explorer.
        """
        block = WebDriverWait(self.driver, 10)
        block.until(EC.presence_of_element_located(
            (By.ID, folder_id)))
        folder_elem = self.driver.find_element_by_id(folder_id)
        hover = ActionChains(self.driver).move_to_element(folder_elem)
        hover.perform()
        time.sleep(self.micro_wait)  # seems to be necessary (! jQuery animations?)
        class_ = 'backbone-file-explorer-directory_icon_button'
        if is_file:
            class_ = 'backbone-file-explorer-directory_entry_name'
        folder_id = folder_id.replace('.', r'\.')
        selector = 'div#{} span.{}'.format(folder_id, class_)
        span_elem = self.driver.find_element_by_css_selector(selector)
        hover = ActionChains(self.driver).move_to_element(span_elem)
        hover.perform()
        span_elem.click()
        # When clicking a "file", we are in the Review AIP interface and we
        # don't need to wait for the file's contents to be visible because no
        # contents.
        if is_file:
            return
        try:
            folder_contents_selector = \
                'div#{} + div.backbone-file-explorer-level'.format(folder_id)
            block = WebDriverWait(self.driver, 10)
            block.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, folder_contents_selector)))
        except TimeoutException:
            self.click_folder_old_browser(folder_id)


def get_xpath_matches_folder_text(folder_text):
    """Return the XPath to match a folder in the file browser whose name
    starts with the text ``folder_text`` and where the substring after
    ``folder_text`` starts with "(". Yay XPath contortionism!

    Previously returned XPath:

    return ("div[contains(@class, 'tree-label') and"
            " descendant::span[contains(text(), '{}')]]"
            .format(folder_text))
    """
    return (
        "div[contains(@class, 'tree-label') and"
        " descendant::span[starts-with(normalize-space(text()), '{0}') and"
        " starts-with(normalize-space(substring-after("
        "normalize-space(text()),"
        " '{0}')), '(')]]".format(folder_text))


def folder_label2icon_xpath(folder_label_xpath):
    """Given XPATH for TS folder label, return XPATH for its folder
    icon.
    """
    return "{}/preceding-sibling::i[@class='tree-branch-head']".format(
        folder_label_xpath)


def folder_label2children_xpath(folder_label_xpath):
    """Given XPATH for TS folder label, return XPATH for its children
    <treeitem> element."""
    return '{}/following-sibling::treeitem'.format(folder_label_xpath)
