import logging
from logging.handlers import RotatingFileHandler

class LogManager:
    def __init__(self, unique_key='NO_KEY_PROVIDED', log_file="audit_log/cv_llm.log", max_bytes=5 * 1024 * 1024, level=logging.DEBUG):
        """
        Initialize a logger with RotatingFileHandler.

        :param unique_key: A unique identifier for the logs.
        :param log_file: Path to the log file.
        :param max_bytes: Maximum size of a log file before rotation (in bytes).
        :param level: Logging level (e.g., logging.INFO, logging.DEBUG).
        """
        self.unique_key = unique_key
        self.logger = logging.getLogger(log_file)

        if not self.logger.hasHandlers():  # Avoid adding multiple handlers
            self.logger.setLevel(level)

            #create a rotating file handler
            handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=3
            )
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(unique_key)s - %(name)s - %(levelname)s - %(message)s"
                )
            )

            #add the handler to the logger
            self.logger.addHandler(handler)

    def get_logger(self):
        """
        Returns the configured logger instance with `unique_key` as default extra.
        """
        return logging.LoggerAdapter(self.logger, {'unique_key': self.unique_key})
