# coding: utf8
import logging


class CtrlC(Exception):
    """ Custom exception raised when a Ctrl + C interrupt is received """

    def __init__(self, v="type ctrl c"):
        logger = logging.getLogger(__name__)
        logger.debug('CtrlC triggered')
        self.value = v

    def __str__(self):
        return repr(self.value)


class CtrlD(Exception):
    """ Custom exception raised when a Ctrl + D interrupt is received """

    def __init__(self, v="type ctrl d"):
        logger = logging.getLogger(__name__)
        logger.debug('CtrlD triggered')
        self.value = v

    def __str__(self):
        return repr(self.value)
