from data_binding.database_engine import ConcreteConnectionManager
from utils.config_loader import load_config

def get_connection_manager():
    # Load the configuration
    config = load_config()
    connection_config = config.get('connection', {})
    return ConcreteConnectionManager(connection_config)