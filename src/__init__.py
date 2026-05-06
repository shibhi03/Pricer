from .core.config_loader import load_config
from .core.driver import create_driver
from .logger import setup_logger


config = load_config()

logger = setup_logger(config)

driver = create_driver(config)