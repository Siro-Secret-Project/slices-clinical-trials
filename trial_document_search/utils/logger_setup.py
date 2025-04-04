import logging


class Logger:
    def __init__(self, name="trial_document_search", level=logging.DEBUG):
        """
        Initializes a logger with a console handler.
        :param name: Name of the logger
        :param level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create console handler if not already added
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)

            # Define log format
            formatter = logging.Formatter("%(levelname)s: - %(name)s - %(asctime)s-  %(message)s")
            console_handler.setFormatter(formatter)

            # Add handler to logger
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger


# Usage
logger = Logger().get_logger()
logger.debug("Logger Setup Completed !!!")
