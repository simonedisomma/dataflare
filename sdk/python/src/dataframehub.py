# dfhub.py
import yaml
from dataset.sqllite_driver import SQLiteDriver

class DataFrameHub:

    def __init__(self, config_file: str):
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

    def from_source(self, source: str):
        source_config = self.config[source]
        driver_class = globals()[source_config['driver']]
        return driver_class(source_config['db_url'])
