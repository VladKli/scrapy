import datetime

from selenium import webdriver
import scrapy
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from scrapy.http import HtmlResponse
from chemicals.driver import get_selenium_driver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AstatechincComSpider(scrapy.Spider):
    """Spider for crawling the astatechinc.com website.

        This Spider is responsible for crawling the astatechinc.com website to extract chemical
        information. It uses Selenium to interact with the website and Scrapy to handle the crawling
        logic.
    """

    name = "astatechinc_com"
    allowed_domains = ["astatechinc.com"]
    base_url = "https://www.astatechinc.com/CATALOG.php"

    driver = get_selenium_driver()
    second_driver = get_selenium_driver(page_load_strategy=True)

    def __init__(self, *args, **kwargs):
        """Initialize the Spider instance.

        This method is called when the Spider instance is created. It calls the
        superclass's __init__ method and sets the start_urls attribute to the list
        of start URLs obtained from the get_start_urls method.
        """
        super(AstatechincComSpider, self).__init__(*args, **kwargs)
        self.start_urls = self.get_start_urls()

    def get_start_urls(self):
        """Collects and returns the start URLs for the Spider.

            This function retrieves the start URLs by scraping the website's categories
            and subcategories using a Selenium WebDriver. It visits the base URL, extracts
            the categories' names, and collects their corresponding URLs. It also handles
            another type of categories and adds their URLs to the final list.

            Returns:
                list: A list of URLs representing the start URLs for the Spider.

            Raises:
                TimeoutException: If a timeout occurs while loading a page.
            """
        categories_names = []
        another_categories = []
        categories_urls = []
        driver = self.driver
        driver.get(self.base_url)
        all_cats = driver.find_element(By.ID, "masterdiv").find_elements(
            By.XPATH, ".//div"
        )
        for el in all_cats:
            onclick_attr = el.get_attribute("onclick")
            if onclick_attr and "SwitchMenu" in onclick_attr:
                categories_names.append(el.text)
            else:
                another_categories.append(el.text)

        for el in categories_names:
            base_div = driver.find_element(By.XPATH, f"//div[contains(text(), '{el}')]")
            try:
                driver.execute_script("arguments[0].click();", base_div)
            except TimeoutException:
                continue
            submenu_span = base_div.find_element(By.XPATH, "./following-sibling::span")
            a_tags = submenu_span.find_elements(By.XPATH, ".//a")
            a_tag_texts = [a_tag.text for a_tag in a_tags]
            for sub_category in a_tag_texts:
                categories_urls.append(
                    self.get_subcategory_url(driver, el, sub_category)
                )

        for el in another_categories:
            category = driver.find_element(By.XPATH, f'//*[contains(text(), "{el}")]')
            try:
                driver.execute_script("arguments[0].click();", category)
                categories_urls.append(driver.current_url)
            except TimeoutException:
                self.logger.error(
                    "Timeout occurred while loading the page: %s", driver.current_url
                )
                return None

        # all_pages = self.get_all_pages(driver, categories_urls)
        #
        # categories_urls = list(set(categories_urls + all_pages))

        driver.quit()

        # Return the collected links as start URLs for the Spider
        return categories_urls

    def get_subcategory_url(self, driver, category_name, sub_category_name):
        """Retrieve the URL of a specific subcategory.

            This function takes a Selenium WebDriver instance, the name of a category, and the name
            of a subcategory. It navigates to the website's base URL, clicks on the specified category,
            clicks on the specified subcategory, and returns the URL of the subcategory page.

            Args:
                driver (WebDriver): An instance of the Selenium WebDriver.
                category_name (str): The name of the category containing the desired subcategory.
                sub_category_name (str): The name of the subcategory for which to retrieve the URL.

            Returns:
                str: The URL of the subcategory page.

            Raises:
                TimeoutException: If a timeout occurs while loading a page.
            """
        try:
            driver.get(self.base_url)
            category = driver.find_element(
                By.XPATH, f"//div[contains(text(), '{category_name}')]"
            )
            driver.execute_script("arguments[0].click();", category)
            sub_category = driver.find_element(
                By.XPATH, f"//a[contains(text(), '{sub_category_name}')]"
            )
            driver.execute_script("arguments[0].click();", sub_category)
            return driver.current_url
        except TimeoutException:
            return driver.current_url

    def parse(self, response):
        """Parse the main page response and extract links to be processed.

            This function is the main parsing method for the Spider. It receives the
            response from the main page and extracts the desired links from the HTML
            table using XPath selectors. For each link, it creates a Scrapy `Request`
            object with the URL and a callback function `parse_link` to process the
            link further.

            Args:
                response (scrapy.http.Response): The response object of the main page.

            Yields:
                scrapy.Request: A Scrapy `Request` object representing a link to be processed.
            """
        table = response.xpath("/html/body/div[9]/div[2]/div[5]/table[1]")
        a_tags = table.xpath(".//a")

        for link in a_tags:
            href = link.xpath("@href").get()
            yield scrapy.Request(url=href, callback=self.parse_link)

    def parse_link(self, response):
        """Parse the individual link page response and extract the desired data.

            This function is responsible for parsing the response of an individual link page.
            It uses XPath selectors to extract the required data from the HTML response. The
            extracted data includes information such as CAS number, availability, quantities,
            units, currency, and price. The function yields a dictionary containing the extracted
            data as a Scrapy `Item` to be further processed or stored.

            Args:
                response (scrapy.http.Response): The response object of the link page.

            Yields:
                dict: A dictionary containing the extracted data as a Scrapy `Item`.
            """
        qt_list = []
        unit_list = []
        currency_list = []
        price_pack_list = []
        n = 1
        driver = self.second_driver
        try:
            driver.get(response.url)
            page_source = driver.page_source
        except TimeoutException:
            self.logger.error(
                "Timeout occurred while loading the page: %s", response.url
            )
            return None

        response = HtmlResponse(url=response.url, body=page_source, encoding="utf-8")
        try:
            numcas = response.xpath(
                '//td[contains(text(), "CAS")]/following-sibling::td[1]/text()'
            ).get()
            if not numcas:
                return None

            availability = self.get_availability(driver)

            tr_tags = response.xpath(
                '//tr[.//span[contains(text(), "Please enter Qty to check availability")]]'
            )
            for _ in tr_tags:
                qt_and_unit = (
                    response.xpath(f'//span[@id="su{n}"]/text()').get().split("/")
                )
                currency = (
                    response.xpath('//td[contains(text(), "Price")]/text()')
                    .get()
                    .split("(")[-1]
                    .replace(")", "")
                )
                price = response.xpath(f'//input[@id="UnitPrice{n}"]/@value').get()
                qt_list.append(qt_and_unit[0])
                unit_list.append(qt_and_unit[1])
                currency_list.append(currency)
                price_pack_list.append(price)
                n += 1

            yield {
                "datetime": datetime.datetime.now(),
                "availability": True if availability else False,
                "company_name": "AstaTech",
                "product_url": response.url,
                "numcas": numcas,
                "name": response.xpath(
                    '//td[contains(text(), "Compound")]/following-sibling::td[1]/text()'
                )
                .get()
                .strip(),
                "qt_list": qt_list,
                "unit_list": unit_list,
                "currency_list": currency_list,
                "price_pack_list": price_pack_list,
            }

        except Exception:
            return None

    def get_all_pages(self, driver, categories_urls):
        """Retrieve all the pages for each category.

           This function takes a Selenium WebDriver instance and a list of category URLs.
           It navigates to each category URL, iterates through the pages within the category,
           and collects the URLs of all the pages. The function returns a list containing all
           the collected page URLs.

           Args:
               driver (WebDriver): An instance of the Selenium WebDriver.
               categories_urls (list): A list of category URLs.

           Returns:
               list: A list of all the collected page URLs.
           """
        all_pages = []
        for category in categories_urls:
            driver.get(category)

            contain_products = True
            while contain_products:
                table_element = driver.find_element(
                    By.XPATH,
                    "//table[@style='table-layout:fixed; margin-top:0px; border:1px solid #CCC;' and @width='552px']",
                )
                number_of_products = table_element.find_elements(By.XPATH, ".//div")
                next_page = driver.find_element(
                    By.XPATH,
                    "/html/body/div[9]/div[2]/div[5]/table[2]/tbody/tr/td[3]/a",
                )
                all_pages.append(driver.current_url)
                if len(number_of_products) == 12:
                    try:
                        driver.execute_script("arguments[0].click();", next_page)
                    except TimeoutException:
                        continue
                else:
                    contain_products = False
        return all_pages

    def get_availability(self, driver):
        """Check the availability of a product.

            This function takes a Selenium WebDriver instance and checks the availability
            of a product by filling the quantity input fields with a value of 1 and waiting
            for the "in stock" message to be visible. If the product is available, it returns
            True. Otherwise, it returns False.

            Args:
                driver (WebDriver): An instance of the Selenium WebDriver.

            Returns:
                bool: True if the product is available, False otherwise.
            """
        qty_inputs = self.second_driver.find_elements(By.XPATH, "//input[@value=0]")
        for qty_input in qty_inputs:
            qty_input.clear()
            qty_input.send_keys("1")
            try:
                is_available = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, '//span[contains(text(), "in stock")]')
                    )
                )
            except TimeoutException:
                continue
            if is_available:
                return True
        return False

    def spider_closed(self, spider):
        """Callback function called when the spider is closed.

            This function is called when the spider is being closed. It is responsible for
            performing cleanup tasks, such as closing the WebDriver. If the `second_driver`
            instance exists, it is closed by calling the `quit()` method. The function also
            logs a message to indicate that all links have been processed.

            Args:
                spider (scrapy.Spider): The Spider instance being closed.
            """
        if self.second_driver:
            self.second_driver.quit()
        self.logger.info("Finished processing all links!")
