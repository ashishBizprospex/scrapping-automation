import scrapy
from datetime import datetime
import scrapy
import pandas as pd
import os
import re
from sqlalchemy import create_engine
from datetime import datetime
import sys
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_config import DatabaseConfig

class QuotesSpider(scrapy.Spider):
    name = "PEP-Scraper_nbim"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_mstr = pd.DataFrame()
        self.final = pd.DataFrame()
        self.target_path = "ResultantScrape" + str(random.randint(0, 1000)) + ".xlsx"
        self.db_config = DatabaseConfig()
        self.engine = create_engine(
            f"postgresql://{self.db_config.PG_USER}:{self.db_config.PG_PASSWORD}@"
            f"{self.db_config.PG_HOST}:{self.db_config.PG_PORT}/{self.db_config.PG_DATABASE}"
        )

    def insert_mstr_data(self):
        # Insert all collected scraped data to the database
        if not self.final_mstr.empty:
            self.final_mstr.to_sql(self.db_config.MSTR_TABLE_NAME, self.engine, if_exists='append', index=False)
            # print(f"Data inserted successfully into {self.db_config.TABLE_NAME}")
        else:
            print("No data to insert.")

    def insert_data(self):
        # Insert all collected scraped data to the database
        if not self.final.empty:
            self.final.to_sql(self.db_config.TABLE_NAME, self.engine, if_exists='append', index=False)
            # print(f"Data inserted successfully into {self.db_config.TABLE_NAME}")
        else:
            print("No data to insert.")
    # def reformat_date(date_str):
    #     # Parse the input date in DD.MM.YYYY format
    #     date_obj = datetime.strptime(date_str, "%d.%m.%Y")
    #     # Format it to DD-MM-YYYY
    #     return date_obj.strftime("%d-%m-%Y")

    def start_requests(self):
        url = "https://www.nbim.no/en/responsible-investment/ethical-exclusions/exclusion-of-companies/"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):


        rows = response.xpath('//tbody/tr')
        for row in rows:
            name = row.xpath('.//span[@class="nbim-responsive-table--value"]/a/text()').get()
            if name:
                name = name.strip()

            category = row.xpath('.//td[3]/span[@class="nbim-responsive-table--value"]/text()').get().strip()

            if category:
                category = category.strip()

            criterion = row.xpath('.//td[4]/span[@class="nbim-responsive-table--value"]/text()').get()
            if criterion :
                criterion = criterion.strip()

            decision = row.xpath('.//td[5]/span[@class="nbim-responsive-table--value"]/text()').get()
            if decision:
                decision = decision.strip()

            publishing_date = row.xpath('.//td[6]/span[@class="nbim-responsive-table--value"]/text()').get()
            if publishing_date:
                publishing_date = publishing_date.strip()
                date_obj = datetime.strptime(publishing_date, "%d.%m.%Y")
                publishing_date = date_obj.strftime("%d-%m-%Y")

            data = {
                'reference_number': "-",
                'type': "Entity",
                'name': "-" if not name else name,
                'aliases': "-",
                'date_of_birth': "-",
                'citizenship': "-",
                'countries': "Norway",
                'addresses': "-",
                'identifiers_passport_number': "-",
                'sanctions': "-",
                'phones': "-",
                'emails': "-",
                'dataset_list_name': "Norges Bank Investment Management observation and exclusion of companies",
                'source_url': "https://www.nbim.no/"
            }
            new_data = pd.DataFrame([data])
            self.final_mstr = pd.concat([self.final_mstr, new_data], ignore_index=True)

            data1 = {
                'reference_number': "-",
                'type': "Entity",
                'name': "-" if not name else name,
                'aliases': "-",
                'date_of_birth': "-",
                'citizenship': "-",
                'countries': "Norway",
                'addresses': "-",
                'identifiers_passport_number': "-",
                'sanctions': "-",
                'phones': "-",
                'emails': "-",
                'dataset_list_name': "Norges Bank Investment Management observation and exclusion of companies",
                'source_url': "https://www.nbim.no/",
                'category': "-" if not category else category,
                'criterion':  "-" if not criterion else criterion,
                'decision': "-" if not decision else decision,
                'publishing_date': "-" if not publishing_date else publishing_date
            }
            new_data_1 = pd.DataFrame([data1])
            self.final = pd.concat([self.final, new_data_1], ignore_index=True)

            self.final.to_excel(self.target_path, index=False)
            # yield data

    def closed(self, reason):
        self.insert_mstr_data()
        self.insert_data()
        print("closed")