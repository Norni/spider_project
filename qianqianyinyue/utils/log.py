import logging
import sys
from qianqianyinyue.settings import LOG_FMT, LOG_LEVEL, LOG_DATE_FMT, LOG_FILENAME


class Logger(object):
    def __init__(self):
        self._logger = logging.getLogger()
        self.formatter = logging.Formatter(fmt=LOG_FMT, datefmt=LOG_DATE_FMT)
        self._logger.addHandler(hdlr=self.get_file_handler(filename=LOG_FILENAME))
        self._logger.addHandler(hdlr=self.get_console_handler())
        self._logger.setLevel(level=LOG_LEVEL)

    def get_file_handler(self, filename):
        file_handler = logging.FileHandler(filename=filename, encoding='utf8')
        file_handler.setFormatter(fmt=self.formatter)
        return file_handler

    def get_console_handler(self):
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(fmt=self.formatter)
        return console_handler

    @property
    def logger(self):
        return self._logger


logger = Logger().logger

if __name__ == "__main__":
    logger.info("哈哈哈")
