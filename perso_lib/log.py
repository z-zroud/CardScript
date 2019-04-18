import os
import sys
import logging
import logging.handlers
from colorama import Fore, Back, Style
import colorama

LEVELS = {'NOSET': logging.NOTSET,
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL}

class Singleton(object):
    _instance = None
    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

class Log(Singleton):
    # create logs file folder
    @staticmethod
    def init(file_name = "log.txt", log_level = "NOSET"):
        logger = logging.getLogger()
        colorama.init()
        logs_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(logs_dir) or not os.path.isdir(logs_dir):
            os.makedirs(logs_dir)

        # clear old root logger handlers
        logging.getLogger().handlers = []

        file_name = os.path.join(logs_dir, file_name)
        
        # define a rotating file handler
        rotatingFileHandler = logging.handlers.RotatingFileHandler(filename =file_name, maxBytes = 1024 * 1024 * 50,backupCount = 5)
        formatter = logging.Formatter("%(message)s")
        rotatingFileHandler.setFormatter(formatter)
        logger.addHandler(rotatingFileHandler)
        
        logger.setLevel(LEVELS[log_level.upper()])

    @staticmethod
    def info(fmt,*arg,end='\n'):
        console_fmt = '%s' + fmt
        print(console_fmt % (Fore.GREEN,*arg),end=end)
        logging.info(fmt,*arg)

    @staticmethod
    def warn(fmt,*arg,end='\n'):
        console_fmt = '%s' + fmt
        print(console_fmt % (Fore.YELLOW,*arg),end=end)
        logging.info('[warn]:' + fmt,*arg)

    @staticmethod
    def debug(fmt,*arg,end='\n'):
        console_fmt = '%s' + fmt
        print(console_fmt % (Fore.BLUE,*arg),end=end)
        logging.info(fmt,*arg)

    @staticmethod
    def error(fmt,*arg,end='\n'):
        console_fmt = '%s' + fmt
        print(console_fmt % (Fore.RED,*arg),end=end)
        logging.info('[error]:' + fmt,*arg)


if __name__ == "__main__":
    log = Log()
    log.init('D:\\a.txt')
    log.info('%s','xxxx')
    log.debug('%s','debug')
    log.warn('%s','warn')
    log.error("%s",'error')
