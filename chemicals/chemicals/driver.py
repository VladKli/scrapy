from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_selenium_driver(page_load_strategy=False):
    """Get a Selenium WebDriver instance.

        This function creates and returns a Selenium WebDriver instance using the Chrome
        driver. The function accepts an optional argument `page_load_strategy` to set the
        page load strategy of the WebDriver. By default, the page load strategy is set to
        "normal". If `page_load_strategy` is set to `True`, the page load strategy is set
        to "eager".

        Args:
            page_load_strategy (bool, optional): The page load strategy of the WebDriver.
                Defaults to False.

        Returns:
            selenium.webdriver.Chrome: The Selenium WebDriver instance.
        """
    chrome_options = Options()
    if page_load_strategy:
        chrome_options.page_load_strategy = "eager"
    driver = webdriver.Chrome(options=chrome_options)
    return driver
