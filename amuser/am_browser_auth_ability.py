"""Archivematica Authentication Ability"""
import logging

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import selenium_ability


logger = logging.getLogger("amuser.authentication")


class ArchivematicaBrowserAuthenticationAbility(
    selenium_ability.ArchivematicaSeleniumAbility
):
    """Archivematica Authentication Ability: the ability of an Archivematica user to
    use a browser to login/out to/from Archivematica and/or the Storage Service.
    """

    def login(self):
        """Login to Archivematica."""
        self.driver.get(self.get_login_url())
        username_input_id = "id_username"
        password_input_id = "id_password"
        try:
            element_present = EC.presence_of_element_located((By.ID, username_input_id))
            WebDriverWait(self.driver, self.pessimistic_wait).until(element_present)
        except TimeoutException:
            logger.warning("Timed out when waiting for login page to load")
        username_elem = self.driver.find_element_by_id(username_input_id)
        username_elem.send_keys(self.am_username)
        password_elem = self.driver.find_element_by_id(password_input_id)
        password_elem.send_keys(self.am_password)
        submit_button_elem = self.driver.find_element_by_tag_name("button")
        submit_button_elem.click()

    def login_ss(self):
        """Login to Archivematica Storage Service."""
        self.driver.get(self.get_ss_login_url())
        username_input_id = "id_username"
        password_input_id = "id_password"
        try:
            element_present = EC.presence_of_element_located((By.ID, username_input_id))
            WebDriverWait(self.driver, self.pessimistic_wait).until(element_present)
        except TimeoutException:
            logger.warning("Timed out when waiting for SS login page to load")
        username_elem = self.driver.find_element_by_id(username_input_id)
        username_elem.send_keys(self.ss_username)
        password_elem = self.driver.find_element_by_id(password_input_id)
        password_elem.send_keys(self.ss_password)
        submit_button_elem = self.driver.find_element_by_css_selector(
            "input[type=submit]"
        )
        submit_button_elem.click()
