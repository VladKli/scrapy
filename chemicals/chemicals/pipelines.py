# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import datetime
import psycopg2
from scrapy.exceptions import DropItem
from chemicals.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class ChemicalsPipeline:
    def process_item(self, item, spider):
        """Process the scraped item.

        This function is called for each scraped item. It processes the item by limiting
        the size of certain attributes to 5 elements, removing non-numeric elements from
        'qt_list' and corresponding elements from 'unit_list', 'currency_list', and
        'price_pack_list', and filtering the 'unit_list' based on a specified list of
        valid units. If the resulting 'qt_list' is empty, the item is discarded by raising
        a `DropItem` exception.

        Args:
            item (scrapy.Item): The scraped item to be processed.
            spider (scrapy.Spider): The Spider instance that generated the item.

        Returns:
            scrapy.Item: The processed item.

        Raises:
            DropItem: If the 'qt_list' is empty after processing.
        """
        item["qt_list"] = item["qt_list"][:5]
        item["unit_list"] = item["unit_list"][:5]
        item["currency_list"] = item["currency_list"][:5]
        item["price_pack_list"] = item["price_pack_list"][:5]

        qt_list = []
        unit_list = []
        currency_list = []
        price_pack_list = []
        for qt, unit, currency, price in zip(
            item["qt_list"],
            item["unit_list"],
            item["currency_list"],
            item["price_pack_list"],
        ):
            if "*" in qt:
                continue
            if isinstance(float(qt), float):
                qt_list.append(float(qt.strip()))
                unit_list.append(unit.strip())
                currency_list.append(currency.strip())
                price_pack_list.append(price.strip())
        item["qt_list"] = qt_list
        item["unit_list"] = unit_list
        item["currency_list"] = currency_list
        item["price_pack_list"] = price_pack_list

        valid_units = ["mg", "g", "kg", "ml", "l"]
        filtered_unit_list = []
        filtered_qt_list = []
        filtered_currency_list = []
        filtered_price_pack_list = []
        for qt, unit, currency, price in zip(
            item["qt_list"],
            item["unit_list"],
            item["currency_list"],
            item["price_pack_list"],
        ):
            if unit.strip().lower() in valid_units:
                filtered_unit_list.append(unit.strip().lower())
                filtered_qt_list.append(float(qt))
                filtered_currency_list.append(currency)
                filtered_price_pack_list.append(price)
        item["unit_list"] = filtered_unit_list
        item["qt_list"] = filtered_qt_list
        item["currency_list"] = filtered_currency_list
        item["price_pack_list"] = filtered_price_pack_list

        if not item["qt_list"]:
            raise DropItem("Item discarded due to empty 'qt_list'")

        return item


class PostgreSQLPipeline:
    def __init__(self):
        """Initialize the Spider.

           This method is called when the Spider instance is created. It establishes a connection
           to the PostgreSQL database using the provided connection details (host, port, dbname,
           user, password), and creates a cursor object to perform database operations.
        """
        self.conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        """Process the scraped item.

        This function is called for each scraped item. It processes the item by inserting
        its data into a PostgreSQL database table named 'scrapy_app_chemicals'. The item
        data is inserted into the table using an SQL INSERT statement. If any error occurs
        during the database operation, the transaction is rolled back and a `DropItem`
        exception is raised.

        Args:
            item (scrapy.Item): The scraped item to be processed.
            spider (scrapy.Spider): The Spider instance that generated the item.

        Returns:
            scrapy.Item: The processed item.

        Raises:
            DropItem: If an error occurs during the database operation.
        """
        try:
            self.cursor.execute(
                "INSERT INTO scrapy_app_chemicals (datetime, availability, company_name, product_url, numcas, name, "
                "qt_list, unit_list, currency_list, price_pack_list) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    item["datetime"],
                    item["availability"],
                    item["company_name"],
                    item["product_url"],
                    item["numcas"],
                    item["name"],
                    item["qt_list"],
                    item["unit_list"],
                    item["currency_list"],
                    item["price_pack_list"],
                ),
            )
            self.conn.commit()
        except (psycopg2.Error, KeyError) as e:
            self.conn.rollback()
            raise DropItem(f"Error inserting item into PostgreSQL: {str(e)}")
        return item

    def close_spider(self, spider):
        """Close the Spider.

        This method is called when the Spider is closed. It is responsible for closing
        the database connection and cursor.

        Args:
            spider (scrapy.Spider): The Spider instance being closed.
        """
        self.cursor.close()
        self.conn.close()
