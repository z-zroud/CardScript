# -*- coding: utf-8 -*-
'''
Modified on 2012-11-27
@summary: clear old root logger handlers when reconfig logging
@author: JerryKwan

Created on 2012-06-14 19:50
@summary:  logging config
@author: JerryKwan
'''

import logging

import logging.handlers

import os
import sys

LEVELS = {'NOSET': logging.NOTSET,
          'DEBUG': logging.DEBUG,
          'INFO': logging.INFO,
          'WARNING': logging.WARNING,
          'ERROR': logging.ERROR,
          'CRITICAL': logging.CRITICAL}

#set up logging to file

#logging.basicConfig(level = logging.NOTSET,
#                    format = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
#                    )

##                    filename = "./log.txt",

##                    filemode = "w")

# create logs file folder
def init(file_name = "log.txt", log_level = "NOSET"):
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(logs_dir) or not os.path.isdir(logs_dir):
        os.makedirs(logs_dir)

    # clear old root logger handlers
    logging.getLogger().handlers = []

    file_name = os.path.join(logs_dir, file_name)
    # define a rotating file handler
    rotatingFileHandler = logging.handlers.RotatingFileHandler(filename =file_name,
                                                      maxBytes = 1024 * 1024 * 50,
                                                      backupCount = 5)
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    rotatingFileHandler.setFormatter(formatter)
    logging.getLogger().addHandler(rotatingFileHandler)

    # define a handler whitch writes messages to sys
    console = logging.StreamHandler()
    # set a format which is simple for console use
    formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger("").addHandler(console)
    # set initial log level
    logger = logging.getLogger()
    level = LEVELS[log_level.upper()]
    logger.setLevel(level)

def init_ex(file_name = "log.txt", log_level = "NOSET", remote_address = ("127.0.0.1", 8888), write_console = False):
    '''
    @summary: config logging to write logs to remote service
    @param host: hostname or ip address of the log server
    @param port: port to be used for log server
    @log_level: log level
    '''
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if os.path.exists(logs_dir) and os.path.isdir(logs_dir):
        pass
    else:
        os.makedirs(logs_dir)
    # format file name
    if file_name is None:
        file_name = os.path.splitext(sys.argv[0])[0]
        file_name = os.path.join(logs_dir, "%s_%s.log"%(file_name, os.getpid()))
    else:
        file_name = os.path.join(logs_dir, file_name)

    # clear old root logger handlers
    logging.getLogger("").handlers = []
    
    # define a rotating file handler
    rotatingFileHandler = logging.handlers.RotatingFileHandler(filename =file_name,
                                                      maxBytes = 1024 * 1024 * 50,
                                                      backupCount = 5)
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    rotatingFileHandler.setFormatter(formatter)
    # add log handler
    logging.getLogger("").addHandler(rotatingFileHandler)

    if write_console is not None and  write_console == True:
        # define a handler whitch writes messages to sys
        console = logging.StreamHandler()
        console.setLevel(logging.NOTSET)
        # set a format which is simple for console use
        formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add log handler
        logging.getLogger("").addHandler(console)

    if remote_address is not None and hasattr(remote_address, "__iter__") and len(remote_address) > 1:
        # define a socket handler
        socketHandler = logging.handlers.SocketHandler(remote_address[0], remote_address[1])
        formatter = logging.Formatter("%(asctime)s %(processName)s %(process)s %(name)-12s %(levelname)-8s %(message)s")
        socketHandler.setFormatter(formatter)
        # add log handler
        logging.getLogger("").addHandler(socketHandler)

    # set initial log level
    logger = logging.getLogger("")
    level = LEVELS[log_level.upper()]
    logger.setLevel(level)