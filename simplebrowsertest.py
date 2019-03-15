#!/usr/bin/env python3

from selenium import webdriver
from selenium.common.exceptions import WebDriverException


TEST_URL = "https://www.artefactual.com"
TEST_TITLE = "Artefactual Systems Inc."


def get_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(chrome_options=options)
    driver.set_window_size(1700, 900)
    return driver


def get_firefox_driver():
    fp = webdriver.FirefoxProfile()
    fp.set_preference("dom.max_chrome_script_run_time", 0)
    fp.set_preference("dom.max_script_run_time", 0)
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(firefox_profile=fp, firefox_options=options)
    return driver


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
