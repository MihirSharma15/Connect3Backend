import logging

"""Logger for logging errors."""

consolehandle = logging.StreamHandler()
consolehandle.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
consolehandle.setFormatter(formatter)


# Returns the logger based on which file its in
def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(consolehandle)
    return logger
