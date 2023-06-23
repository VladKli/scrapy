import datetime
import time

from selenium import webdriver
import scrapy
from selenium.webdriver.common.by import By


class AstatechincComSpider(scrapy.Spider):
    name = "astatechinc_com"
    allowed_domains = ["astatechinc.com"]
    start_urls = []
    base_url = 'https://www.astatechinc.com/CATALOG.php'

    def __init__(self, *args, **kwargs):
        super(AstatechincComSpider, self).__init__(*args, **kwargs)
        self.start_urls = self.get_start_urls()

    def get_start_urls(self):
        categories_names = []
        another_categories = []
        categories_urls = []
        driver = webdriver.Chrome()
        driver.get(self.base_url)
        all_cats = driver.find_element(By.ID, "masterdiv").find_elements(By.XPATH, ".//div")
        for el in all_cats:
            onclick_attr = el.get_attribute("onclick")
            if onclick_attr and "SwitchMenu" in onclick_attr:
                categories_names.append(el.text)
            else:
                another_categories.append(el.text)

        for el in categories_names:
            base_div = driver.find_element(By.XPATH, f"//div[contains(text(), '{el}')]")
            driver.execute_script("arguments[0].click();", base_div)
            submenu_span = base_div.find_element(By.XPATH, "./following-sibling::span")
            a_tags = submenu_span.find_elements(By.XPATH, ".//a")
            a_tag_texts = [a_tag.text for a_tag in a_tags]
            for sub_category in a_tag_texts:
                categories_urls.append(self.get_subcategory_url(driver, el, sub_category))
            print('done')

        for el in another_categories:
            category = driver.find_element(By.XPATH, f'//*[contains(text(), "{el}")]')
            driver.execute_script("arguments[0].click();", category)
            categories_urls.append(driver.current_url)

        driver.quit()

        # Return the collected links as start URLs for the Spider
        return categories_urls

    def get_subcategory_url(self, driver, category_name, sub_category_name):
        driver.get(self.base_url)
        category = driver.find_element(By.XPATH, f"//div[contains(text(), '{category_name}')]")
        driver.execute_script("arguments[0].click();", category)
        sub_category = driver.find_element(By.XPATH, f"//a[contains(text(), '{sub_category_name}')]")
        driver.execute_script("arguments[0].click();", sub_category)
        return driver.current_url

    def parse(self, response):
        qt_list = []
        unit_list = []
        currency_list = []
        price_pack_list = []
        n = 1

        availability = response.xpath('//*[contains(text(), "Ready to ship within 24 hours")]').get()

        tr_tags = response.xpath('//tr[.//span[contains(text(), "Please enter Qty to check availability")]]')
        for _ in tr_tags:

            qt_and_unit = response.xpath(f'//span[@id="su{n}"]/text()').get().split('/')
            currency = response.xpath('//td[contains(text(), "Price")]/text()').get().split('(')[-1].replace(')', '')
            price = response.xpath(f'//input[@id="UnitPrice{n}"]/@value').get()
            qt_list.append(qt_and_unit[0])
            unit_list.append(qt_and_unit[1])
            currency_list.append(currency)
            price_pack_list.append(price)
            n += 1

        yield {
            'datetime': datetime.datetime.now(),
            'availability': True if availability else False,
            'company_name': 'AstaTech',
            'product_url': None,
            'numcas': response.xpath('//td[contains(text(), "CAS")]/following-sibling::td[1]/text()').get(),
            'name': response.xpath('//td[contains(text(), "Compound")]/following-sibling::td[1]/text()').get(),
            'qt_list': qt_list,
            'unit_list': unit_list,
            'currency_list': currency_list,
            'price_pack_list': price_pack_list,
        }
