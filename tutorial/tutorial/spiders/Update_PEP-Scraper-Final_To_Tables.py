import time

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
import logging
logging.basicConfig(level=logging.INFO)
from sqlalchemy import create_engine, Table, MetaData, insert, select, func, update
from pathlib import Path
from sqlalchemy import create_engine, Table, MetaData, Column, String, BigInteger, UniqueConstraint, inspect, text
from sqlalchemy.orm import declarative_base
from typing import Type
from db_config import DatabaseConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base = declarative_base()

class PepPerson(Base):
    __tablename__ = 'aml_pep_person'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    name = Column(String, nullable=False)
    aliases = Column(String, nullable=True)
    date_of_birth = Column(String(50), nullable=True)
    citizenship = Column(String(200), nullable=True)
    countries = Column(String(200), nullable=True)
    addresses = Column(String, nullable=True)
    identifiers_passport_number = Column(String, nullable=True)
    sanctions = Column(String, nullable=True)
    phones = Column(String(200), nullable=True)
    emails = Column(String(200), nullable=True)
    dataset_list_name = Column(String(200), nullable=True)
    source_url = Column(String(200), nullable=True)
    reference_number = Column(String(200), nullable=True)

    __table_args__ = (
        UniqueConstraint('name', 'type', name='idx_name_type_aml_pep_person'),
    )

class PepSpecificTarget(Base):
    __tablename__ = 'aml_pep_nbim_norway_entity'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    name = Column(String, nullable=False)
    aliases = Column(String, nullable=True)
    date_of_birth = Column(String(50), nullable=True)
    citizenship = Column(String(200), nullable=True)
    countries = Column(String(200), nullable=True)
    addresses = Column(String, nullable=True)
    identifiers_passport_number = Column(String, nullable=True)
    sanctions = Column(String, nullable=True)
    phones = Column(String(200), nullable=True)
    emails = Column(String(200), nullable=True)
    dataset_list_name = Column(String(200), nullable=True)
    source_url = Column(String(200), nullable=True)
    reference_number = Column(String(200), nullable=True)
    category = Column(String(200), nullable=True)
    criterion = Column(String, nullable=True)
    decision = Column(String(200), nullable=True)
    publishing_date = Column(String(10), nullable=True)
    # test_column = Column(String(200), nullable=True)
    __table_args__ = (
        UniqueConstraint('name', 'type', name='idx_name_type_aml_pep_nbim_norway_entity'),
    )

class DatabaseConnector:
    def __init__(self, db_config):
        self.db_config = db_config
        self.engine = create_engine(
            f"postgresql://{self.db_config.PG_USER}:{self.db_config.PG_PASSWORD}@"
            f"{self.db_config.PG_HOST}:{self.db_config.PG_PORT}/{self.db_config.PG_DATABASE}"
        )
        self.metadata = MetaData()
        self.metadata.bind = self.engine

    def init_schemas(self):
        """Check if schemas exist and create them if they don't"""
        logger.info("Checking and initializing database schemas...")
        inspector = inspect(self.engine)

        # Check if tables exist
        existing_tables = inspector.get_table_names()

        if self.db_config.MSTR_TABLE_NAME not in existing_tables:
            logger.info(f"Creating master table: {self.db_config.MSTR_TABLE_NAME}")
            PepPerson.__table__.create(self.engine)
        else:
            logger.info(f"Table {self.db_config.MSTR_TABLE_NAME} already exists")

        if self.db_config.TABLE_NAME not in existing_tables:
            logger.info(f"Creating table: {self.db_config.TABLE_NAME}")
            PepSpecificTarget.__table__.create(self.engine)
        else:
            logger.info(f"Table {self.db_config.TABLE_NAME} already exists")
            # Check if new columns need to be added
            self.update_table_schema(self.db_config.TABLE_NAME, PepSpecificTarget)
        self.metadata.reflect(bind=self.engine)
        logger.info("Schema initialization completed")

    def update_table_schema(self, table_name: str, model_class: Type[Base]):
        """Add missing columns to an existing table with explicit commit"""
        inspector = inspect(self.engine)
        existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
        model_columns = {col.name for col in model_class.__table__.columns}

        missing_columns = model_columns - existing_columns
        if missing_columns:
            logger.info(f"Adding missing columns to {table_name}: {missing_columns}")
            conn = self.engine.connect()
            trans = conn.begin()  # Start a transaction
            try:
                for column in missing_columns:
                    column_def = getattr(model_class, column)
                    alter_cmd = f"ALTER TABLE {table_name} ADD COLUMN {column} {column_def.type.compile(self.engine.dialect)}"
                    conn.execute(text(alter_cmd))
                trans.commit()  # Commit only if no exceptions
                logger.info(f"Added missing columns to {table_name}: {missing_columns}")
            except Exception as e:
                logger.error(f"Failed to add columns: {e}")
                trans.rollback()
                raise
            finally:
                conn.close()

class QuotesSpider(scrapy.Spider):
    name = "PEP-Scraper_nbim-Updated"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_mstr = []
        self.final = []
        self.target_path = "ResultantScrape" + str(random.randint(0, 1000)) + ".xlsx"
        self.db_config = DatabaseConfig()
        self.db_connector = DatabaseConnector(self.db_config)
        self.db_connector.init_schemas()  # Initialize schemas upon startup

    def insert_data(self):
        conn = self.db_connector.engine.connect()
        table = Table(self.db_config.TABLE_NAME, self.db_connector.metadata, autoload_with=self.db_connector.engine)
        for row in self.final:
            try:
                existing_row = conn.execute(
                    table.select().where(
                        (table.c.name == row['name']) & (table.c.type == row['type'])
                    )
                ).fetchone()

                if existing_row:
                    conn.execute(
                        table.update()
                        .where((table.c.name == row['name']) & (table.c.type == row['type']))
                        .values(**row)
                    )
                else:
                    conn.execute(table.insert().values(**row))
            except Exception as e:
                print(f"Error processing row {row}: {e}")
        conn.commit()
        conn.close()

    def insert_mstr_data(self):
        conn = self.db_connector.engine.connect()
        table = Table(self.db_config.MSTR_TABLE_NAME, self.db_connector.metadata, autoload_with=self.db_connector.engine)
        for row in self.final_mstr:
            try:
                existing_row = conn.execute(
                    table.select().where(
                        (table.c.name == row['name']) & (table.c.type == row['type'])
                    )
                ).fetchone()

                if existing_row:
                    conn.execute(
                        table.update()
                        .where((table.c.name == row['name']) & (table.c.type == row['type']))
                        .values(**row)
                    )
                else:
                    conn.execute(table.insert().values(**row))
            except Exception as e:
                print(f"Error processing row {row}: {e}")
        conn.commit()
        conn.close()


    def start_requests(self):
        url = "https://www.nbim.no/en/responsible-investment/ethical-exclusions/exclusion-of-companies/"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # filename = f"nbim-{random.randint(1, 10000)}.html"
        # Path(filename).write_bytes(response.body)
        # self.log(f"Saved file {filename}")


        print("status",response.status)
        rows = response.xpath('//*[@id="table-a16379ec-8bd5-4480-b4fb-b1425894bc76"]/table/tbody/tr')
        print("len of records", len(rows))
        # for row in rows:
        for idx, row in enumerate(rows):
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
            if criterion :
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

                data1 = {
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
                    'source_url': "https://www.nbim.no/",
                    'category': "-" if not category else category,
                    'criterion':  "-" if not criterion else criterion,
                    'decision': "-" if not decision else decision,
                    'publishing_date': "-" if not publishing_date else publishing_date,
                    # 'test_column': "Test value",
                }
                # new_data_1 = pd.DataFrame([data1])
                # self.final = pd.concat([self.final, new_data_1], ignore_index=True)
                self.final.append(data1)

                # self.final.to_excel(self.target_path, index=False)
                df1 = pd.DataFrame(self.final)
                df1.to_excel(self.target_path, index=False)
            # yield data

    def closed(self, reason):
        print(f"Final: {len(self.final)}")
        print(f"Final MSTR: {len(self.final_mstr)}")
        self.insert_mstr_data()
        time.sleep(5)
        self.insert_data()
        print("closed")