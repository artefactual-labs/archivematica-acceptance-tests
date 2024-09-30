#!/usr/bin/env python3
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

TEST_URL = "https://www.artefactual.com"
TEST_TITLE = "Home | Artefactual"


def get_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=old")
    driver = webdriver.Chrome(options=options)
    return driver


def get_firefox_driver():
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
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
