#!/usr/bin/env python3
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


TEST_URL = "https://www.artefactual.com"
TEST_TITLE = "Home - Artefactual"


def get_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--whitelisted-ips")
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
    print(f"{name}... ", end="")
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
    return 0


if __name__ == "__main__":
    print("Starting tests...")
    chrome_result = run_test(get_chrome_driver, "Chrome")
    firefox_result = run_test(get_firefox_driver, "Firefox")
    exit(chrome_result or firefox_result)
