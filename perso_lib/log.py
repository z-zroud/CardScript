import os
import sys
import logging
import logging.handlers

LEVELS = {'NOSET': logging.NOTSET,
          'DEBUG': logging.DEBUG,
          'INFO': logging.INFO,
          'WARNING': logging.WARNING,
          'ERROR': logging.ERROR,
          'CRITICAL': logging.CRITICAL}


# create logs file folder
def init(file_name = "log.txt", log_level = "NOSET"):
    logs_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(logs_dir) or not os.path.isdir(logs_dir):
        os.makedirs(logs_dir)

    # clear old root logger handlers
    logging.getLogger().handlers = []

    file_name = os.path.join(logs_dir, file_name)
    # define a rotating file handler
    rotatingFileHandler = logging.handlers.RotatingFileHandler(filename =file_name,
                                                      maxBytes = 1024 * 1024 * 50,
                                                      backupCount = 5)
    #formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    formatter = logging.Formatter("%(message)s")
    rotatingFileHandler.setFormatter(formatter)
    logging.getLogger().addHandler(rotatingFileHandler)

    # define a handler whitch writes messages to sys
    console = logging.StreamHandler()
    # set a format which is simple for console use
    #formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
    formatter = logging.Formatter("%(message)s")
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger("").addHandler(console)
    # set initial log level
    logger = logging.getLogger()
    level = LEVELS[log_level.upper()]
    logger.setLevel(level)