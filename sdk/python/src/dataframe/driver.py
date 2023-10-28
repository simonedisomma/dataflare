import pandas as pd
from abc import ABC, abstractmethod

class DataFrameDriver(ABC):

    @abstractmethod
    def fetch_data(self, query: str) -> pd.DataFrame:
        pass

        