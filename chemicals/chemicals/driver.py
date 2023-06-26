from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_selenium_driver(page_load_strategy=False):
    chrome_options = Options()
    if page_load_strategy:
        chrome_options.page_load_strategy = 'eager'
    driver = webdriver.Chrome(options=chrome_options)
    return driver
