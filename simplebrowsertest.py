#!/usr/bin/env python3

from os import environ

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.options import Options as FirefoxOptions


TEST_URL = "https://www.artefactual.com"
TEST_TITLE = "Artefactual Systems Inc."


def get_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(chrome_options=options)
    driver.set_window_size(1700, 900)
    return driver


def get_firefox_driver():
    profile = webdriver.FirefoxProfile()
    profile.set_preference("dom.max_chrome_script_run_time", 0)
    profile.set_preference("dom.max_script_run_time", 0)
    options = FirefoxOptions()
    options.add_argument('-headless')
    return webdriver.Firefox(
        firefox_profile=profile,
        firefox_options=options,
        log_path="/home/archivematica/geckodriver.log")


def run_test(driver_getter, name):
    print("{}... ".format(name), end="")
    try:
        driver = driver_getter()
    except WebDriverException as err:
        print("error!", err)
        return 1
    try:
        driver.get(TEST_URL)
        assert driver.title == TEST_TITLE
        print("success!")
        print("Capabilities:", driver.capabilities)
    except Exception as err:
        print("error!", err)
        return 1
    finally:
        driver.quit()


if __name__ == "__main__":
    print("Starting tests...")
    run_test(get_chrome_driver, "Chrome")
    run_test(get_firefox_driver, "Firefox")

