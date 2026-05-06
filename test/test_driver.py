    
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.driver import create_driver
from src.core.config_loader import load_config
import log_tests
import time

config = load_config()

logger = log_tests.setup_test_logger(config)
print(logger)

driver = create_driver(config)

driver.get("https://www.google.com")
logger.info("Opened Google homepage")

time.sleep(5)

driver.quit()
logger.info("Closed the browser")