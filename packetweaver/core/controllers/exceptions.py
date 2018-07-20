

class ExitPw(Exception):
    """ Exception to cleanly exit the application on error """
    pass


class Conf(Exception):
    pass


class ConfNone(Conf):
    pass


class ConfHistFile(Conf):
    pass


class ConfHistFileNotAccessible(ConfHistFile):
    """ Warn that the file used to store the interactive CLI history
    is not accessible """
    pass


class ConfEditor(Conf):
    pass


class ConfEditorNone(Conf):
    """ Warn about the fact no editor configuration has been specified """
    pass


class ConfEditorInvalid(ConfEditor):
    """ Warn about an invalid editor command in the Tools section of
    the framework configuration file"""
    pass


class ConfDep(Conf):
    """ Exception warning about an error in the "Dependencies" section of
    the framework configuration file """
    pass


class ConfDepNone(ConfNone):
    """ Exception used to warn that no dependencies are specified in
    the framework configuration file """
    pass


class ConfDepNotExists(ConfDep):
    """ Exception used to warn that a path to a python dependency
    does not exists """
    pass


class ConfDepNotDir(ConfDep):
    """ Exception used to warn that a path to a python dependency does not
    point to a directory """
    pass


class ConfPkg(Conf):
    """ Exception warning about an error in the "Packages" section of
    the framework configuration file """
    pass


class ConfPkgNone(ConfNone):
    """ Exception used to warn that the framework configuration file does not
    activate any ability package """
    pass


class ConfPkgAbl(ConfPkg):
    """ Exception used to warn that an ability package path is not
    precise enough """
    pass


class ConfPkgNotExists(ConfPkg):
    """ Exception used to warn that an ability package path does not
    exists """
    pass


class ConfPkgNotDir(ConfPkg):
    """ Exception used to warn that an ability package path is not
    a directory """
    pass
