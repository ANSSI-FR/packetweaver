# coding: utf8


class CtrlC(Exception):
    """ Custom exception raised when a Ctrl + C interrupt is received """

    def __init__(self, v="type ctrl c"):
        self.value = v

    def __str__(self):
        return repr(self.value)


class CtrlD(Exception):
    """ Custom exception raised when a Ctrl + D interrupt is received """

    def __init__(self, v="type ctrl d"):
        self.value = v

    def __str__(self):
        return repr(self.value)
