# workflows/base_workflow.py

from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime
from typing import Any  

class BaseWorkflow(ABC):
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None

    def log_start(self):
        self.start_time = datetime.now()
        print(f"Started workflow '{self.name}' at {self.start_time}")

    def log_end(self):
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        print(f"Finished workflow '{self.name}' at {self.end_time}")
        print(f"Duration: {duration}")

    @abstractmethod
    def fetch_data(self) -> Any:
        """
        Fetch raw data from the source.
        
        Returns:
            Any: The raw data fetched from the source
        """
        pass

    @abstractmethod
    def process_data(self, raw_data: Any) -> pd.DataFrame:
        """
        Process the raw data into a pandas DataFrame.
        
        Args:
            raw_data (Any): The raw data returned by fetch_data
        
        Returns:
            pd.DataFrame: The processed data
        """
        pass

    @abstractmethod
    def run(self) -> pd.DataFrame:
        """
        Run the complete workflow.
        
        Returns:
            pd.DataFrame: The final processed data
        """
        pass