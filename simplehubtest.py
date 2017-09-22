#!/usr/bin/env python3

from os import environ

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


HUB_ADDRESS = environ.get('HUB_ADDRESS', 'http://localhost:4444/wd/hub')


TEST_URL = "https://www.artefactual.com"
TEST_TITLE = "Artefactual Systems Inc."

chrome = webdriver.Remote(
    command_executor=HUB_ADDRESS,
    desired_capabilities=DesiredCapabilities.CHROME)

firefox = webdriver.Remote(
    command_executor=HUB_ADDRESS,
    desired_capabilities=DesiredCapabilities.FIREFOX)

print("Starting tests...")

print("Chrome... ", end="")
chrome.get(TEST_URL)
assert chrome.title == TEST_TITLE
print("OK!")
chrome.quit()

print("Firefox... ", end="")
firefox.get(TEST_URL)
assert firefox.title == TEST_TITLE
print("OK!")
firefox.quit()
