# coding: utf8
import abc


class ViewInterface(object):
    """ Abstract base class defining the interface for pw views """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def warning(self, t): pass

    @abc.abstractmethod
    def info(self, t): pass

    @abc.abstractmethod
    def error(self, t): pass

    @abc.abstractmethod
    def fail(self, t): pass

    @abc.abstractmethod
    def debug(self, t): pass

    @abc.abstractmethod
    def success(self, t): pass

    @abc.abstractmethod
    def help(self, t): pass

    @abc.abstractmethod
    def progress(self, t): pass
