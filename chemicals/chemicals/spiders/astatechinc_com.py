from datetime import datetime
import scrapy


class AstatechincComSpider(scrapy.Spider):
    """
    Spider for scraping data from the 'astatechinc.com' website.
    """

    name = "astatechinc_com"
    allowed_domains = ["astatechinc.com"]
    start_urls = ["https://www.astatechinc.com/"]

    domain = "https://www.astatechinc.com/"

    def parse(self, response):
        """
        Parses the initial response and extracts category names.
        Sends requests to parse each category separately.
        """
        categories_tags = response.xpath('//a[contains(@onclick, "TTT")]')
        categories_names = [name.xpath("text()").get() for name in categories_tags]

        for name in categories_names:
            url = f"https://www.astatechinc.com/ConcordCatagory.php?CCatagory={name}"
            yield scrapy.Request(url, callback=self.parse_category)

    def parse_category(self, response):
        """
        Parses the category page and extracts chemical URLs.
        Sends requests to get the redirect links for each chemical.
        If there are more pages, sends request to the next page of the category.
        """
        chemicals = response.xpath('//a[contains(@href, "cat=")]')
        for chemical in chemicals:
            url = chemical.xpath("@href").get()
            yield scrapy.Request(url, callback=self.get_redirect_link)

        if self.check_if_last_page(response):
            next_page = (
                self.domain
                + response.xpath('//a[contains(text(), "Next")]/@href').get()
            )
            yield scrapy.Request(next_page, callback=self.parse_category)

    def get_redirect_link(self, response):
        """
        Extracts the redirect link and sends a request to parse the chemical details.
        """
        url = response.text.split("window.parent.location='")[1].split("'")[0]
        yield scrapy.Request(self.domain + url, callback=self.parse_chemical)

    def check_if_last_page(self, response):
        """
        Checks if the current page is the last page in the category.
        Returns True if it's not the last page, False otherwise.
        """
        pages = response.xpath(
            '//span[@style="margin-right:0.3em;"]/following-sibling::text()'
        ).get()
        pages = pages[2:-2].split(" of ")
        current_page, last_page = pages[0], pages[1]
        return last_page != current_page

    def get_availability_urls(self, response):
        """
        Extracts the availability URLs for each chemical.
        Returns a list of URLs.
        """
        n = 1
        urls = []
        all_units = response.xpath(
            '//tr[.//span[contains(text(), "Please enter Qty to check availability")]]'
        )
        for unit in all_units:
            catalog = response.css("#Catalog::text").get()
            size = unit.css(f"#su{n}::text").get()
            url = f"https://astatechinc.com/CGetInv.php?Catalog={catalog}&SUX={size}&QTY=1&QTYX={n}"
            urls.append(url)
            n += 1
        return urls

    def parse_chemical(self, response):
        """
        Parses the chemical details page and yields the extracted data.
        Sends requests to check the availability of the chemical.
        """
        qt_list = []
        unit_list = []
        currency_list = []
        price_pack_list = []
        n = 1

        numcas = response.xpath(
            '//td[contains(text(), "CAS")]/following-sibling::td[1]/text()'
        ).get()
        if not numcas:
            return None

        availability_urls = self.get_availability_urls(response)

        tr_tags = response.xpath(
            '//tr[.//span[contains(text(), "Please enter Qty to check availability")]]'
        )
        for _ in tr_tags:
            qt_and_unit = response.xpath(f'//span[@id="su{n}"]/text()').get().split("/")
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

        item = {
            "datetime": datetime.now(),
            "availability": [],
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

        yield from self.process_additional_requests(availability_urls, item)

    def process_additional_requests(self, urls, item):
        """
        Processes additional requests to check the availability of the chemical.
        Yields the item with updated availability information.
        """
        if not urls:
            if True in item["availability"]:
                item["availability"] = True
            else:
                item["availability"] = False

            yield item
        else:
            url = urls[0]
            remaining_urls = urls[1:]
            yield scrapy.Request(
                url,
                callback=self.get_availability,
                meta={"urls": remaining_urls, "item": item},
            )

    def get_availability(self, response):
        """
        Extracts availability information from the response and updates the item.
        Sends requests for remaining availability URLs.
        """
        item = response.meta["item"]

        if "in stock" in response.text or "in China stock" in response.text:
            item["availability"].append(True)
        else:
            item["availability"].append(False)

        remaining_urls = response.meta["urls"]
        yield from self.process_additional_requests(remaining_urls, item)
