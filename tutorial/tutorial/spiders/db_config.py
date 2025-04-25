# PG_HOST = 'localhost'
# PG_PORT = 5432
# PG_USER = 'rahulrathore'
# PG_PASSWORD = 'password'
# PG_DATABASE = 'nodelogin'
# TABLE_NAME = 'aml_pep_person'
class DatabaseConfig:
    def __init__(self):
        self.PG_HOST = 'localhost'
        self.PG_PORT = 5432
        self.PG_USER = 'rahulrathore'
        self.PG_PASSWORD = 'password'
        self.PG_DATABASE = 'nodelogin'
        self.MSTR_TABLE_NAME = 'aml_pep_person'
        self.TABLE_NAME = 'aml_pep_nbim_norway_entity'

    def get_db_credentials(self):
        return {
            'host': self.PG_HOST,
            'port': self.PG_PORT,
            'user': self.PG_USER,
            'password': self.PG_PASSWORD,
            'database': self.PG_DATABASE
        }