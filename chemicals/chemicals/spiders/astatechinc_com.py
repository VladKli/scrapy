from datetime import datetime
import scrapy

class AstatechincComSpider(scrapy.Spider):

    name = "astatechinc_com"
    allowed_domains = ["astatechinc.com"]
    start_urls = ["https://www.astatechinc.com/"]

    domain = "https://www.astatechinc.com/"


    def parse(self, response):
        categories_tags = response.xpath('//a[contains(@onclick, "TTT")]')
        categories_names = [name.xpath('text()').get() for name in categories_tags]

        for name in categories_names:
            url = f"https://www.astatechinc.com/ConcordCatagory.php?CCatagory={name}"
            yield scrapy.Request(url, callback=self.parse_category)



    def parse_category(self, response):

        chemicals = response.xpath('//a[contains(@href, "cat=")]')
        for chemical in chemicals:
            url = chemical.xpath('@href').get()
            yield scrapy.Request(url, callback=self.get_redirect_link)

        if self.check_if_last_page(response):
            next_page = self.domain+response.xpath('//a[contains(text(), "Next")]/@href').get()
            yield scrapy.Request(next_page, callback=self.parse_category)

    def get_redirect_link(self, response):

        url = response.text.split("window.parent.location='")[1].split("'")[0]
        yield scrapy.Request(self.domain + url, callback=self.parse_chemical)

    def parse_chemical(self, response):

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

        availability = self.get_availability_text(response)

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
            "datetime": datetime.now(),
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

    def check_if_last_page(self, response):
        pages = response.xpath('//span[@style="margin-right:0.3em;"]/following-sibling::text()').get()[2:-2].split(' of ')
        current_page = pages[0]
        last_page = pages[1]
        if last_page != current_page:
            return True
        return False

    def get_availability_text(self, response):
        n = 1

        all_units = response.xpath('//tr[.//span[contains(text(), "Please enter Qty to check availability")]]')
        for unit in all_units:
            catalog = response.css('#Catalog::text').get()
            size = unit.css(f'#su{n}::text').get()
            url = f"https://astatechinc.com/CGetInv.php?Catalog={catalog}&SUX={size}&QTY=1&QTYX={n}"
            n += 1
            yield scrapy.Request(url, callback=self.get_availability)
            print('doo')

    def get_availability(self, response):
            data = response
            print('done')
