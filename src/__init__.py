from .core.config_loader import load_config
from .logger import setup_logger


config = load_config()

logger = setup_logger(config)