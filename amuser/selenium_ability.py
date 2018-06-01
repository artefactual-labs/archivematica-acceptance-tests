"""Selenium Ability"""

import logging
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

from . import base


logger = logging.getLogger('amuser.selenium')


class ArchivematicaSeleniumError(base.ArchivematicaUserError):
    pass


class ArchivematicaSeleniumAbility(base.Base):
    """Archivematica Selenium Ability: common, reusable Selenium-based
    functionality for superclasses.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver = None
        self.all_drivers = []

    def get_driver(self):
        if self.driver_name == 'Chrome':
            driver = webdriver.Chrome()
            driver.set_window_size(1700, 900)
        elif self.driver_name == 'Chrome-Hub':
            capabilities = DesiredCapabilities.CHROME.copy()
            capabilities["chrome.switches"] = [
                "--start-maximized",
                '--ignore-certificate-errors',
                '--test-type']
            driver = webdriver.Remote(
                command_executor=os.environ.get('HUB_ADDRESS'),
                desired_capabilities=capabilities)
            driver.set_window_size(1200, 900)
        elif self.driver_name == 'Firefox':
            fp = webdriver.FirefoxProfile()
            fp.set_preference("dom.max_chrome_script_run_time", 0)
            fp.set_preference("dom.max_script_run_time", 0)
            os.environ['MOZ_HEADLESS'] = '1'
            binary = FirefoxBinary('firefox', log_file=sys.stdout)
            driver = webdriver.Firefox(firefox_binary=binary)
            #driver = webdriver.Firefox(firefox_profile=fp)
        elif self.driver_name == 'Firefox-Hub':
            driver = webdriver.Remote(
                command_executor=os.environ.get('HUB_ADDRESS'),
                desired_capabilities=DesiredCapabilities.FIREFOX)
        else:
            driver = getattr(webdriver, self.driver_name)()
        driver.set_script_timeout(self.apathetic_wait)
        self.all_drivers.append(driver)
        return driver

    def set_up(self):
        self.driver = self.get_driver()
        # Do not maximize window in Chrome to workaround:
        # https://bugs.chromium.org/p/chromedriver/issues/detail?id=1901
        if self.driver_name not in ('Chrome-Hub', 'Chrome'):
            self.driver.maximize_window()

    def tear_down(self):
        """Tear down by closing all of the browser windows, clearing the
        temporary directory, and quitting all drivers.
        TODO: figure out why in some cases (with some browsers, e.g., Firefox)
        the following call to ``self.driver.window_handles`` causes Selenium to
        hang indefinitely.
        """
        if self.driver_name != 'Firefox':
            for window_handle in self.driver.window_handles:
                self.driver.switch_to.window(window_handle)
                self.driver.quit()
        self.clear_tmp_dir()
        for driver in self.all_drivers:
            try:
                driver.quit()
            except WebDriverException:
                pass

    def navigate(self, url, reload=False):
        """Navigate to ``url``; login and try again, if redirected."""
        if self.driver.current_url == url and not reload:
            return
        self.driver.get(url)
        if self.driver.current_url == url:
            return
        if self.driver.current_url != url:
            if self.driver.current_url.endswith('/installer/welcome/'):
                self.setup_new_install()
            else:
                if url.startswith(self.ss_url):
                    self.login_ss()
                else:
                    self.login()
        self.driver.get(url)

    def wait_for_new_window(self, handles_before, timeout=None):
        timeout = timeout or self.apathetic_wait
        def window_handles_count_has_changed(driver):
            logger.info('Previously we had %s window handles, now we have'
                        ' %s', len(handles_before), len(driver.window_handles))
            return len(handles_before) != len(driver.window_handles)
        WebDriverWait(self.driver, timeout).until(
            window_handles_count_has_changed)

    def hover(self, elem):
        hover = ActionChains(self.driver).move_to_element(elem)
        hover.perform()

    def wait_for_presence(self, crucial_element_css_selector, timeout=None):
        """Wait until the element matching ``crucial_element_css_selector``
        is present.
        """
        self.wait_for_existence(EC.presence_of_element_located,
                                crucial_element_css_selector, timeout=timeout)

    def wait_for_invisibility(self, crucial_element_css_selector,
                              timeout=None):
        """Wait until the element matching ``crucial_element_css_selector``
        is *not* visible.
        """
        self.wait_for_existence(EC.invisibility_of_element_located,
                                crucial_element_css_selector, timeout=timeout)

    def wait_for_visibility(self, crucial_element_css_selector, timeout=None):
        """Wait until the element matching ``crucial_element_css_selector``
        is visible.
        """
        self.wait_for_existence(EC.visibility_of_element_located,
                                crucial_element_css_selector, timeout=timeout)

    def wait_for_existence(self, existence_detector,
                           crucial_element_css_selector, timeout=None):
        """Wait until the element matching ``crucial_element_css_selector``
        exists, as defined by existence_detector.
        """
        if not timeout:
            timeout = self.pessimistic_wait
        try:
            element_exists = existence_detector(
                (By.CSS_SELECTOR, crucial_element_css_selector))
            WebDriverWait(self.driver, timeout).until(element_exists)
        except TimeoutException:
            logger.warning(
                "Waiting for existence ('presence' or 'visibility') of element"
                " matching selector %s took too much time!",
                crucial_element_css_selector)


def recurse_on_stale(func):
    """Decorator that re-runs a method if it triggers a
    ``StaleElementReferenceException``. This error occurs when AM's JS repaints
    the DOM and we're holding on to now-destroyed elements.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except StaleElementReferenceException:
            return wrapper(*args, **kwargs)
    return wrapper
