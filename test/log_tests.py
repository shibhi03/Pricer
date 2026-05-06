import logging
import os

def setup_test_logger(config):
    logging_config = config["logging"]
    logging_level = logging_config.get("level", logging.INFO).upper()
    logging_file = logging_config.get("test_file", "logs/test.log")
    logging_format = logging_config.get("test_format", "%(asctime)s - %(name)s - %(levelname)s - [TEST] %(message)s")

    os.makedirs(os.path.dirname(logging_file), exist_ok=True)

    logging.basicConfig(
        level=logging_level,
        format=logging_format,
        handlers=[
            logging.FileHandler(logging_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)