import logging
import os

def setup_logger(config):
    logging_config = config["logging"]
    log_level = logging_config.get("level", logging.INFO).upper()
    log_file = logging_config.get("file", "logs/app.log")
    log_format = logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)