import time
import scrapy
from datetime import datetime
import scrapy
import pandas as pd
import os
import re
from datetime import datetime
import sys
import random
import json
import logging
import tempfile
import shutil
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class QuotesSpider(scrapy.Spider):
    name = "aml_pep_nbim_norway_entity_Test"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_mstr = []
        self.keys = {
            'reference_number': 'reference_number',
            'type': 'type',
            'name': 'name',
            'aliases': 'aliases',
            'date_of_birth': 'date_of_birth',
            'citizenship': 'citizenship',
            'countries': 'countries',
            'addresses': 'addresses',
            'identifiers_passport_number': 'identifiers_passport_number',
            'sanctions': 'sanctions',
            'phones': 'phones',
            'emails': 'emails',
            'dataset_list_name': 'dataset_list_name',
            'source_url': 'source_url'
        }
        # self.temp_dir = tempfile.mkdtemp()

    def start_requests(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
        proxies = [
            'http://brd-customer-hl_fbc4a16a-zone-web_unlocker_tech:a9pkkpoq082f@brd.superproxy.io:33335',
        ]
        proxy = random.choice(proxies)

        url = "https://www.nbim.no/en/responsible-investment/ethical-exclusions/exclusion-of-companies/"
        logger.info(f"Starting crawl for URL: {url}")
        # yield scrapy.Request(url, callback=self.parse)
        yield scrapy.Request(url, headers=headers, callback=self.parse, meta={'url': url, 'proxy': proxy})

    def parse(self, response):
        # filename = f"nbim-{random.randint(1, 10000)}.html"
        # Path(filename).write_bytes(response.body)
        # self.log(f"Saved file {filename}")
        try:
            print("status", response.status)
            logger.info(f"status: {response.status}")
            rows = response.xpath('//*[@id="table-a16379ec-8bd5-4480-b4fb-b1425894bc76"]/table/tbody/tr')
            print("len of records", len(rows))
            logger.info(f"len of records {len(rows)}")
            # for row in rows:
            for idx, row in enumerate(rows[:1]):
                # time.sleep(5)
                name = row.xpath('.//td[1]/a/text() | .//td[1]/a/span/text()').get()
                if name:
                    name = name.strip()

                aliases = row.xpath('.//td[2]/text()').get()
                if aliases:

                    if "Former" in aliases:
                        aliases = str(aliases).replace("Former", "").strip()
                    else:
                        aliases = aliases.strip()
                else:
                    aliases = ""
                category = row.xpath('.//td[3]/text()').get()
                if category:
                    category = category.strip()

                criterion = row.xpath('.//td[4]/text()').get()
                if criterion:
                    criterion = criterion.strip()

                decision = row.xpath('.//td[5]/text()').get()
                if decision:
                    decision = decision.strip()

                publishing_date = row.xpath('.//td[6]/text()').get()
                if publishing_date:
                    publishing_date = publishing_date.strip()
                    date_obj = datetime.strptime(publishing_date, "%d.%m.%Y")
                    publishing_date = date_obj.strftime("%d-%m-%Y")
                if name:
                    name = str(name).strip()
                    data = {
                        'reference_number': "-",
                        'type': "Entity",
                        'name': name,
                        'aliases': "-" if not aliases else aliases,
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
                    # new_data = pd.DataFrame([data])
                    # self.final_mstr = pd.concat([self.final_mstr, new_data], ignore_index=True)
                    self.final_mstr.append(data)
        except Exception as e:
            print(f"Error occurred: {e}")
            logger.error(f"Error processing entry on {response.url}: {e}",exc_info=True)

    def closed(self, reason):
        logger.info(f"Spider closed: {reason}")
        logger.info(f"Total records extracted: {len(self.final_mstr)}")
        print(f"Final MSTR: {len(self.final_mstr)}")
        if self.final_mstr:
            print("Final Data Extracted:", json.dumps(self.final_mstr, indent=4))
        else:
            print("No data extracted.")

        # try:
        #     api_url = "http://localhost:5000/api/scrapdata/v1/save-scrap-data"
        #     headers = {"Content-Type": "application/json"}
        #     payload = {"scrapedData": self.final_mstr, "keys": self.keys}
        #
        #     response = requests.post(api_url, json=payload, headers=headers)
        #
        #     if response.status_code == 200:
        #         print("? Data sent successfully!")
        #     else:
        #         print(f"? Failed to send data! Status Code: {response.status_code}, Response: {response.text}")
        # except Exception as api_error:
        #     print(f"? API Error: {str(api_error)}")
        # shutil.rmtree(self.temp_dir)
        print("closed")