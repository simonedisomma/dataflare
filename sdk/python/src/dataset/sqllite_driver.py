# sqllite_driver.py
import pandas as pd
from sqlalchemy import create_engine
from driver import DataFrameDriver

class SQLiteDriver(DataFrameDriver):

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def fetch_data(self, query: str) -> pd.DataFrame:
        df = pd.read_sql(query, self.engine)
        return df
